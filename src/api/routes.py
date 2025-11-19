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
from src.database.models import Paper, User
from src.ingestion.arxiv_fetcher import fetch_arxiv_papers
from src.services.redis_cache import cache
from src.services.auth import get_current_user, log_search

logger = logging.getLogger(__name__)
router = APIRouter()

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

@router.get("/")
async def root():
    return {
        "message": "Research Paper Curator API",
        "version": "2.0.0",
        "features": ["authentication", "tracking", "monitoring", "ask"]
    }

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
    """Ask a question and get answer from papers"""
    try:
        question = request.get("question", "")
        
        if not question:
            raise HTTPException(status_code=400, detail="No question provided")
        
        query_lower = question.lower()
        papers = db.query(Paper).filter(
            (Paper.title.ilike(f"%{query_lower}%")) |
            (Paper.abstract.ilike(f"%{query_lower}%"))
        ).limit(3).all()
        
        if not papers:
            arxiv_papers = fetch_arxiv_papers(query=question, max_results=3)
            
            if not arxiv_papers:
                return {
                    "answer": f"I couldn't find papers related to '{question}'. Try searching for specific topics!",
                    "sources": [],
                    "audio_url": None
                }
            
            answer = f"Based on research about '{question}':\n\n"
            sources = []
            
            for i, paper in enumerate(arxiv_papers[:3], 1):
                title = paper.get('title', 'Unknown')
                abstract = paper.get('abstract', '')[:200]
                answer += f"{i}. **{title}**\n{abstract}...\n\n"
                sources.append(f"{title} - {paper.get('url', '')}")
        else:
            answer = f"Based on research about '{question}':\n\n"
            sources = []
            
            for i, paper in enumerate(papers, 1):
                answer += f"{i}. **{paper.title}**\n{paper.abstract[:200]}...\n\n"
                sources.append(f"{paper.title} - {paper.pdf_url or ''}")
        
        answer += "\n\nFor more details, view the full papers in sources."
        
        return {
            "answer": answer,
            "sources": sources,
            "audio_url": None
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