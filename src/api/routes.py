"""
Complete API routes for the RAG system.
Handles all endpoints for search, papers, and system management.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from datetime import datetime
import time

from src.api.dependencies import (
    get_database,
    get_search_engine,
    get_llm_client,
    get_cache,
    get_tracker,
    get_processor
)
from src.database.operations import (
    PaperOperations,
    SearchLogOperations,
    MetricsOperations
)
from src.llm.prompts import PromptTemplates
from src.core.logging_config import app_logger


router = APIRouter()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    use_cache: bool = Field(default=True, description="Use cached results")
    filter_categories: Optional[List[str]] = Field(default=None, description="Filter by categories")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


class Source(BaseModel):
    """Source information."""
    arxiv_id: str
    paper_title: str
    paper_authors: List[str]
    chunk_content: str
    relevance_score: float
    chunk_type: str


class AnswerResponse(BaseModel):
    """Response model for answers."""
    question: str
    answer: str
    sources: List[Source]
    processing_time_ms: float
    cache_hit: bool
    metadata: Dict[str, Any]


class PaperSummary(BaseModel):
    """Summary of a research paper."""
    id: int
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published_date: datetime
    pdf_url: Optional[str]


class PaperDetail(PaperSummary):
    """Detailed paper information."""
    comment: Optional[str]
    journal_ref: Optional[str]
    doi: Optional[str]
    primary_category: str
    created_at: datetime
    indexed: Optional[datetime]


class SearchResultItem(BaseModel):
    """Single search result."""
    arxiv_id: str
    paper_title: str
    paper_authors: List[str]
    chunk_content: str
    relevance_score: float
    paper_categories: List[str]


class SearchResponse(BaseModel):
    """Response for search queries."""
    query: str
    results: List[SearchResultItem]
    total_results: int
    processing_time_ms: float


class ProcessingStats(BaseModel):
    """Processing statistics."""
    total_papers: int
    indexed_papers: int
    total_chunks: int
    opensearch_documents: int
    opensearch_size_mb: float


class SystemHealth(BaseModel):
    """System health status."""
    status: str
    components: Dict[str, str]
    timestamp: datetime


# ============================================
# QUESTION ANSWERING ENDPOINTS
# ============================================

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_database),
    search_engine = Depends(get_search_engine),
    llm_client = Depends(get_llm_client),
    cache = Depends(get_cache),
    tracker = Depends(get_tracker)
):
    """
    Ask a question and get an answer with sources.
    
    Pipeline:
    1. Check cache
    2. Hybrid search for relevant chunks
    3. Generate answer with LLM
    4. Track metrics
    5. Cache result
    """
    try:
        start_time = time.time()
        cache_hit = False
        
        # Start trace
        trace = tracker.trace_query(
            query=request.question,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata={"top_k": request.top_k}
        )
        
        app_logger.info(f"Processing question: {request.question}")
        
        # 1. Check cache
        if request.use_cache:
            cache_start = time.time()
            cached_result = cache.get_cached_search_result(
                request.question,
                request.top_k
            )
            cache_latency = (time.time() - cache_start) * 1000
            
            tracker.track_cache(trace, request.question, cached_result is not None, cache_latency)
            
            if cached_result:
                cache_hit = True
                total_time = (time.time() - start_time) * 1000
                
                app_logger.info(f"Cache HIT - Returning cached result ({total_time:.2f}ms)")
                
                tracker.finalize_trace(trace, cached_result, total_time)
                
                return AnswerResponse(
                    **cached_result,
                    cache_hit=True,
                    processing_time_ms=total_time
                )
        
        # 2. Hybrid search
        search_start = time.time()
        search_results = search_engine.search(
            query=request.question,
            top_k=request.top_k,
            filter_categories=request.filter_categories
        )
        search_latency = (time.time() - search_start) * 1000
        
        tracker.track_search(
            trace,
            request.question,
            "hybrid",
            search_results,
            search_latency
        )
        
        if not search_results:
            raise HTTPException(
                status_code=404,
                detail="No relevant papers found for your question"
            )
        
        # 3. Generate answer with LLM
        llm_start = time.time()
        
        system_prompt = PromptTemplates.get_qa_system_prompt()
        prompt = PromptTemplates.build_qa_prompt(request.question, search_results)
        
        answer = llm_client.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3
        )
        
        llm_latency = (time.time() - llm_start) * 1000
        
        tracker.track_llm_generation(
            trace,
            prompt,
            answer,
            llm_client.model,
            llm_latency,
            temperature=0.3
        )
        
        # 4. Format response
        sources = [
            Source(
                arxiv_id=r['arxiv_id'],
                paper_title=r['paper_title'],
                paper_authors=r['paper_authors'],
                chunk_content=r['content'],
                relevance_score=round(r.get('hybrid_score', 0), 4),
                chunk_type=r.get('chunk_type', 'unknown')
            )
            for r in search_results
        ]
        
        total_time = (time.time() - start_time) * 1000
        
        response_data = {
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "processing_time_ms": round(total_time, 2),
            "cache_hit": cache_hit,
            "metadata": {
                "search_latency_ms": round(search_latency, 2),
                "llm_latency_ms": round(llm_latency, 2),
                "num_sources": len(sources),
                "model": llm_client.model
            }
        }
        
        # 5. Cache result
        if request.use_cache:
            cache.cache_search_result(
                request.question,
                request.top_k,
                response_data
            )
        
        # 6. Log search
        SearchLogOperations.log_search(
            db,
            {
                "query": request.question,
                "top_k": request.top_k,
                "search_type": "hybrid",
                "num_results": len(sources),
                "top_paper_ids": [s.arxiv_id for s in sources[:5]],
                "processing_time_ms": total_time,
                "cache_hit": 0,
                "user_id": request.user_id,
                "session_id": request.session_id
            }
        )
        
        # 7. Record metrics
        MetricsOperations.record_metric(
            db,
            "api_latency",
            total_time,
            {"endpoint": "ask"}
        )
        
        tracker.finalize_trace(trace, response_data, total_time)
        
        app_logger.info(f"Question answered in {total_time:.2f}ms")
        
        return AnswerResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error processing question: {e}", exc_info=True)
        
        if trace:
            tracker.track_error(trace, e, "ask_question")
        
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


# ============================================
# SEARCH ENDPOINTS
# ============================================

@router.get("/search", response_model=SearchResponse)
async def search_papers(
    query: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=10, ge=1, le=50),
    search_type: str = Query(default="hybrid", regex="^(vector|keyword|hybrid)$"),
    search_engine = Depends(get_search_engine)
):
    """
    Search for papers without generating an answer.
    
    Args:
        query: Search query
        top_k: Number of results
        search_type: Type of search (vector, keyword, hybrid)
    """
    try:
        start_time = time.time()
        
        app_logger.info(f"Search request: '{query}' (type: {search_type})")
        
        # Perform search
        if search_type == "hybrid":
            results = search_engine.search(query, top_k=top_k)
        elif search_type == "vector":
            from src.embeddings.generator import get_embedding_generator
            embedding_gen = get_embedding_generator()
            query_embedding = embedding_gen.generate_embedding(query)
            results = search_engine.os_client.vector_search(
                query_vector=query_embedding.tolist(),
                top_k=top_k
            )
        else:  # keyword
            results = search_engine.os_client.keyword_search(
                query_text=query,
                top_k=top_k
            )
        
        # Format results
        formatted_results = [
            SearchResultItem(
                arxiv_id=r['arxiv_id'],
                paper_title=r['paper_title'],
                paper_authors=r['paper_authors'],
                chunk_content=r['content'],
                relevance_score=round(r.get('score', r.get('hybrid_score', 0)), 4),
                paper_categories=r.get('paper_categories', [])
            )
            for r in results
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=query,
            results=formatted_results,
            total_results=len(formatted_results),
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        app_logger.error(f"Error in search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# ============================================
# PAPER MANAGEMENT ENDPOINTS
# ============================================

@router.get("/papers", response_model=List[PaperSummary])
async def list_papers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_database)
):
    """List papers with pagination and filtering."""
    try:
        papers = PaperOperations.list_papers(
            db,
            skip=skip,
            limit=limit,
            category=category
        )
        
        return [
            PaperSummary(
                id=p.id,
                arxiv_id=p.arxiv_id,
                title=p.title,
                authors=p.authors,
                abstract=p.abstract,
                categories=p.categories,
                published_date=p.published_date,
                pdf_url=p.pdf_url
            )
            for p in papers
        ]
        
    except Exception as e:
        app_logger.error(f"Error listing papers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{arxiv_id}", response_model=PaperDetail)
async def get_paper(
    arxiv_id: str,
    db: Session = Depends(get_database)
):
    """Get detailed information about a specific paper."""
    try:
        paper = PaperOperations.get_paper_by_arxiv_id(db, arxiv_id)
        
        if not paper:
            raise HTTPException(status_code=404, detail=f"Paper {arxiv_id} not found")
        
        return PaperDetail(
            id=paper.id,
            arxiv_id=paper.arxiv_id,
            title=paper.title,
            authors=paper.authors,
            abstract=paper.abstract,
            categories=paper.categories,
            published_date=paper.published_date,
            pdf_url=paper.pdf_url,
            comment=paper.comment,
            journal_ref=paper.journal_ref,
            doi=paper.doi,
            primary_category=paper.primary_category,
            created_at=paper.created_at,
            indexed=paper.indexed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting paper: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# INGESTION ENDPOINTS
# ============================================

@router.post("/ingest/recent")
async def ingest_recent_papers(
    days_back: int = Query(default=7, ge=1, le=30),
    max_results: int = Query(default=50, ge=1, le=200),
    background_tasks: BackgroundTasks = None,
    processor = Depends(get_processor)
):
    """
    Ingest recent papers from arXiv.
    
    This is a long-running operation that will be executed in the background.
    """
    try:
        app_logger.info(f"Starting ingestion: last {days_back} days, max {max_results} papers")
        
        # Run ingestion in background
        if background_tasks:
            background_tasks.add_task(
                processor.process_recent_papers,
                days_back=days_back,
                max_results=max_results
            )
            
            return {
                "status": "started",
                "message": f"Ingestion started in background for last {days_back} days",
                "max_results": max_results
            }
        else:
            # Run synchronously (not recommended for production)
            stats = processor.process_recent_papers(
                days_back=days_back,
                max_results=max_results
            )
            
            return {
                "status": "completed",
                "stats": stats
            }
            
    except Exception as e:
        app_logger.error(f"Error starting ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/paper/{arxiv_id}")
async def ingest_single_paper(
    arxiv_id: str,
    processor = Depends(get_processor)
):
    """Ingest a single paper by arXiv ID."""
    try:
        from src.ingestion.arxiv_fetcher import get_arxiv_fetcher
        
        fetcher = get_arxiv_fetcher()
        papers = fetcher.fetch_by_ids([arxiv_id])
        
        if not papers:
            raise HTTPException(status_code=404, detail=f"Paper {arxiv_id} not found on arXiv")
        
        result = processor.process_single_paper(papers[0])
        
        return {
            "status": "success",
            "arxiv_id": arxiv_id,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error ingesting paper: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SYSTEM ENDPOINTS
# ============================================

@router.get("/stats", response_model=ProcessingStats)
async def get_stats(
    processor = Depends(get_processor)
):
    """Get system statistics."""
    try:
        stats = processor.get_processing_stats()
        
        return ProcessingStats(
            total_papers=stats.get("total_papers", 0),
            indexed_papers=stats.get("indexed_papers", 0),
            total_chunks=stats.get("total_chunks", 0),
            opensearch_documents=stats.get("opensearch_documents", 0),
            opensearch_size_mb=stats.get("opensearch_size_mb", 0.0)
        )
        
    except Exception as e:
        app_logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/detailed", response_model=SystemHealth)
async def detailed_health_check(
    db: Session = Depends(get_database),
    cache = Depends(get_cache)
):
    """Detailed system health check."""
    try:
        from src.retrieval.opensearch_client import get_opensearch_client
        
        components = {}
        
        # Database
        try:
            db.execute("SELECT 1")
            components["database"] = "healthy"
        except Exception:
            components["database"] = "unhealthy"
        
        # Redis
        components["redis"] = "healthy" if cache.health_check() else "unhealthy"
        
        # OpenSearch
        try:
            os_client = get_opensearch_client()
            os_client.client.ping()
            components["opensearch"] = "healthy"
        except Exception:
            components["opensearch"] = "unhealthy"
        
        # LLM (Ollama)
        try:
            from src.llm.ollama_client import get_ollama_client
            llm = get_ollama_client()
            components["ollama"] = "healthy" if llm._check_connection() else "unhealthy"
        except Exception:
            components["ollama"] = "unhealthy"
        
        # Overall status
        all_healthy = all(status == "healthy" for status in components.values())
        overall_status = "healthy" if all_healthy else "degraded"
        
        return SystemHealth(
            status=overall_status,
            components=components,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        app_logger.error(f"Error in health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(default=None),
    cache = Depends(get_cache)
):
    """Clear cache (all or by pattern)."""
    try:
        if pattern:
            count = cache.clear_pattern(pattern)
            return {"status": "success", "cleared": count, "pattern": pattern}
        else:
            cache.flush_all()
            return {"status": "success", "message": "All cache cleared"}
            
    except Exception as e:
        app_logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(
    cache = Depends(get_cache)
):
    """Get cache statistics."""
    try:
        stats = cache.get_stats()
        return stats
    except Exception as e:
        app_logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))