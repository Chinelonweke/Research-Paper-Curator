"""
API Routes - COMPLETE WITH ASK ENDPOINT
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime
import hashlib

from src.database.connection import get_db
from src.database.models import Paper, PaperChunk, User
from src.ingestion.arxiv_fetcher import fetch_arxiv_papers
from src.services.redis_cache import cache
from src.services.auth import get_current_user, log_search
from src.services.answer_generator import get_answer_generator
from src.services.vector_search import get_vector_search
from src.services.paper_indexer import get_paper_indexer

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def api_root():
    return {
        "message": "Research Paper Curator API",
        "version": "2.0.0",
        "endpoints": {
            "papers": "/api/papers",
            "search": "/api/papers/search",
            "ask": "/api/ask",
            "stats": "/api/papers/stats",
            "health": "/api/health"
        }
    }

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    search_type: str = "hybrid"

class PaperResponse(BaseModel):
    id: str
    title: str
    authors: str
    abstract: str
    url: str
    published: Optional[str] = None
    category: Optional[str] = None

class SearchResponse(BaseModel):
    papers: List[PaperResponse]
    total: int
    search_type: str
    source: str
    cached: bool = False



@router.get("/health")
async def health():
    redis_status = "connected" if cache.client else "disconnected"
    return {
        "status": "healthy",
        "database": "NeonDB",
        "redis": redis_status,
        "airflow": "enabled"
    }

@router.post("/papers/search", response_model=SearchResponse)
async def search_papers(
    request: SearchRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        logger.info(f"🔍 Search by {current_user.username if current_user else 'guest'}: '{request.query}'")
        
        cache_key_hash = hashlib.md5(f"search:{request.query}:{request.limit}".encode()).hexdigest()
        
        cached_result = cache.get(cache_key_hash)
        if cached_result:
            log_search(db, request.query, cached_result['total'], request.search_type, current_user, req)
            return SearchResponse(**cached_result, cached=True)
        
        query_lower = request.query.lower()
        db_papers = db.query(Paper).filter(
            (Paper.title.ilike(f"%{query_lower}%")) |
            (Paper.abstract.ilike(f"%{query_lower}%")) |
            (Paper.authors.ilike(f"%{query_lower}%"))
        ).limit(request.limit).all()
        
        if db_papers and len(db_papers) >= request.limit:
            papers_response = [
                PaperResponse(
                    id=str(p.id),
                    title=p.title,
                    authors=p.authors,
                    abstract=p.abstract,
                    url=p.pdf_url or '',
                    published=p.published_date.strftime('%Y-%m-%d') if p.published_date else None,
                    category=p.primary_category or 'Unknown'
                )
                for p in db_papers
            ]
            
            result = {
                "papers": [p.dict() for p in papers_response],
                "total": len(papers_response),
                "search_type": request.search_type,
                "source": "database"
            }
            
            cache.set(cache_key_hash, result, ttl=3600)
            log_search(db, request.query, len(papers_response), request.search_type, current_user, req)
            
            return SearchResponse(**result, cached=False)
        
        logger.info("📡 Fetching from ArXiv...")
        arxiv_papers = fetch_arxiv_papers(query=request.query, max_results=request.limit)
        
        if not arxiv_papers:
            log_search(db, request.query, 0, request.search_type, current_user, req)
            return SearchResponse(papers=[], total=0, search_type=request.search_type, source="arxiv", cached=False)
        
        for paper_data in arxiv_papers:
            try:
                arxiv_id = paper_data.get('arxiv_id') or paper_data.get('id', 'unknown')
                if not db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first():
                    published_date = None
                    if paper_data.get('published'):
                        try:
                            published_date = datetime.fromisoformat(paper_data['published'].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    new_paper = Paper(
                        arxiv_id=arxiv_id,
                        title=paper_data['title'],
                        authors=paper_data['authors'],
                        abstract=paper_data['abstract'],
                        pdf_url=paper_data['url'],
                        published_date=published_date,
                        primary_category=paper_data.get('category', 'cs.AI'),
                        categories=paper_data.get('category', 'cs.AI'),
                        indexed=True
                    )
                    db.add(new_paper)
            except:
                continue
        
        try:
            db.commit()
        except:
            db.rollback()
        
        papers_response = [PaperResponse(**p) for p in arxiv_papers]
        result = {
            "papers": [p.dict() for p in papers_response],
            "total": len(papers_response),
            "search_type": request.search_type,
            "source": "arxiv"
        }
        
        cache.set(cache_key_hash, result, ttl=3600)
        log_search(db, request.query, len(papers_response), request.search_type, current_user, req)
        
        return SearchResponse(**result, cached=False)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask_question(
    request: dict,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Ask a question and get AI-powered answer using RAG (vector search + LLM)"""
    try:
        question = request.get("question", "")

        if not question:
            raise HTTPException(status_code=400, detail="No question provided")

        logger.info(f"🤖 RAG Question: {question[:50]}...")

        # Try vector search first (RAG with full paper content)
        vector_search = get_vector_search()
        context, sources = vector_search.get_context_for_question(question, db, max_chunks=5)

        if context and sources:
            # Use RAG with chunk context
            logger.info(f"Using RAG with {len(sources)} sources")
            try:
                generator = get_answer_generator()
                answer = generator.generate_answer_from_chunks(question, context, sources)
                return {
                    "answer": answer,
                    "sources": [f"{s['title']} - {s['url']}" for s in sources],
                    "audio_url": None,
                    "rag_mode": True
                }
            except Exception as e:
                logger.warning(f"RAG generation failed: {e}")

        # Fallback: keyword search on abstracts
        logger.info("Falling back to keyword search...")
        stop_words = {'what', 'are', 'the', 'key', 'details', 'in', 'this', 'paper', 'how', 'does', 'is', 'a', 'an', 'of', 'to', 'for', 'and', 'or', 'can', 'you', 'explain', 'describe', 'about', 'tell', 'me'}
        words = [w.strip('?.,!') for w in question.lower().split() if w.strip('?.,!') not in stop_words and len(w) > 2]

        papers = []
        if words:
            from sqlalchemy import or_
            filters = []
            for word in words[:5]:
                filters.append(Paper.title.ilike(f"%{word}%"))
                filters.append(Paper.abstract.ilike(f"%{word}%"))
            papers = db.query(Paper).filter(or_(*filters)).limit(3).all()

        if not papers:
            arxiv_papers = fetch_arxiv_papers(query=question, max_results=3)

            if not arxiv_papers:
                return {
                    "answer": f"I couldn't find papers related to '{question}'. Try searching for specific topics!",
                    "sources": [],
                    "audio_url": None,
                    "rag_mode": False
                }

            paper_dicts = arxiv_papers[:3]
            sources = [f"{p.get('title', '')} - {p.get('url', '')}" for p in paper_dicts]
        else:
            paper_dicts = [
                {"title": p.title, "abstract": p.abstract, "url": p.pdf_url or ""}
                for p in papers
            ]
            sources = [f"{p.title} - {p.pdf_url or ''}" for p in papers]

        # Generate answer using abstracts
        try:
            generator = get_answer_generator()
            answer = generator.generate_answer(question, paper_dicts)
        except Exception as e:
            logger.warning(f"Groq generation failed, using fallback: {e}")
            answer = f"Based on research about '{question}':\n\n"
            for i, p in enumerate(paper_dicts, 1):
                answer += f"{i}. **{p.get('title')}**\n{p.get('abstract', '')[:200]}...\n\n"
            answer += "\n\nFor more details, view the full papers in sources."

        return {
            "answer": answer,
            "sources": sources,
            "audio_url": None,
            "rag_mode": False
        }

    except Exception as e:
        logger.error(f"Ask error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/papers")
async def list_papers(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    try:
        total = db.query(Paper).count()
        papers = db.query(Paper).order_by(Paper.published_date.desc()).offset(skip).limit(limit).all()
        
        return {
            "papers": [
                {
                    'id': str(p.id),
                    'title': p.title,
                    'authors': p.authors,
                    'abstract': p.abstract,
                    'url': p.pdf_url or '',
                    'published': p.published_date.strftime('%Y-%m-%d') if p.published_date else None,
                    'category': p.primary_category or 'Unknown'
                }
                for p in papers
            ],
            "total": total
        }
    except:
        return {"papers": [], "total": 0}

@router.get("/papers/stats")
async def get_stats(db: Session = Depends(get_db)):
    try:
        total = db.query(Paper).count()
        return {
            "total_papers": total,
            "database": "NeonDB",
            "redis": "connected" if cache.client else "disconnected",
            "status": "connected"
        }
    except:
        return {"total_papers": 0, "status": "error"}


# ============== RAG INDEXING ENDPOINTS ==============

@router.post("/papers/{paper_id}/index")
async def index_single_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Index a single paper: download PDF, extract text, chunk, embed"""
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        indexer = get_paper_indexer()
        chunks_created = indexer.index_paper(paper, db)

        return {
            "success": True,
            "paper_id": paper_id,
            "paper_title": paper.title,
            "chunks_created": chunks_created,
            "message": f"Successfully indexed paper with {chunks_created} chunks"
        }

    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/papers/index-all")
async def index_all_papers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Index all unindexed papers in the database"""
    try:
        indexer = get_paper_indexer()
        stats = indexer.index_all_papers(db, only_unindexed=True)

        return {
            "success": True,
            "stats": stats,
            "message": f"Indexed {stats['successful']} papers with {stats['total_chunks']} total chunks"
        }

    except Exception as e:
        logger.error(f"Bulk indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}/chunks")
async def get_paper_chunks(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Get all chunks for a paper"""
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        chunks = db.query(PaperChunk).filter(
            PaperChunk.paper_id == paper_id
        ).order_by(PaperChunk.chunk_index).all()

        return {
            "paper_id": paper_id,
            "paper_title": paper.title,
            "indexed": paper.indexed,
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "id": c.id,
                    "chunk_index": c.chunk_index,
                    "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                    "text_length": len(c.text),
                    "has_embedding": c.embedding is not None
                }
                for c in chunks
            ]
        }

    except Exception as e:
        logger.error(f"Get chunks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/status")
async def get_indexing_status(db: Session = Depends(get_db)):
    """Get overall indexing statistics"""
    try:
        indexer = get_paper_indexer()
        status = indexer.get_indexing_status(db)

        return {
            "success": True,
            **status,
            "rag_enabled": status["total_chunks"] > 0
        }

    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

