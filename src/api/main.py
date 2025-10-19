"""
FastAPI Application - Production Ready with Security & Monitoring.
Combines existing functionality with Phase 2 improvements.
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import psutil
import time
import re

from src.core.config import settings
from src.core.logging_config import app_logger
from src.database.connection import get_db
from src.database.models import Paper, Chunk
from src.database.operations import PaperOperations
from src.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    PerformanceMonitoringMiddleware
)


# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    app_logger.info("="*70)
    app_logger.info(f"🚀 Starting {settings.app_name}")
    app_logger.info(f"📊 Version: {settings.app_version}")
    app_logger.info(f"🌍 Environment: {settings.environment}")
    app_logger.info(f"🗄️  Database: {settings.db_type}")
    app_logger.info(f"🤖 LLM Provider: {settings.llm_provider}")
    app_logger.info(f"🔧 Debug Mode: {settings.debug}")
    app_logger.info("="*70)
    
    # Verify database
    try:
        from src.database.connection import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        app_logger.info("✅ Database connection established")
    except Exception as e:
        app_logger.error(f"❌ Database connection failed: {e}")
        raise
    
    # Verify Redis (if enabled)
    if settings.redis_enabled:
        try:
            from src.cache.redis_cache import get_redis_client
            redis = get_redis_client()
            await redis.ping()
            app_logger.info("✅ Redis cache connected")
        except Exception as e:
            app_logger.warning(f"⚠️  Redis connection failed (will continue without cache): {e}")
    
    app_logger.info("="*70)
    app_logger.info("✅ Application started successfully")
    app_logger.info(f"📡 API running on: http://{settings.api_host}:{settings.api_port}")
    app_logger.info(f"📚 Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    app_logger.info("="*70)
    
    yield
    
    # Shutdown
    app_logger.info("🛑 Shutting down application...")
    from src.database.connection import engine
    engine.dispose()
    app_logger.info("✅ Shutdown complete")


# =============================================================================
# APPLICATION SETUP
# =============================================================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG-based research paper curation with semantic search and Q&A",
    docs_url="/docs" if settings.debug or not settings.is_production else None,
    redoc_url="/redoc" if settings.debug or not settings.is_production else None,
    openapi_url="/openapi.json" if settings.debug or not settings.is_production else None,
    lifespan=lifespan
)


# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page", "X-Process-Time"]
)

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# Performance Monitoring
app.add_middleware(PerformanceMonitoringMiddleware)

# Rate Limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute
)


# Request ID & Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing and request ID."""
    import uuid
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        
        # Log request
        app_logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- {response.status_code} - {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        app_logger.error(f"[{request_id}] Error: {str(e)}", exc_info=True)
        raise


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def serialize_paper(paper: Paper) -> dict:
    """Serialize paper to dictionary."""
    return {
        "id": paper.id,
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": paper.authors_list if hasattr(paper, 'authors_list') else paper.authors,
        "categories": paper.categories_list if hasattr(paper, 'categories_list') else paper.categories,
        "primary_category": paper.primary_category,
        "published_date": paper.published_date.isoformat() if paper.published_date else None,
        "updated_date": paper.updated_date.isoformat() if paper.updated_date else None,
        "pdf_url": paper.pdf_url,
        "comment": paper.comment,
        "journal_ref": paper.journal_ref,
        "doi": paper.doi,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
    }


# =============================================================================
# ROOT & HEALTH ENDPOINTS
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "operational",
        "endpoints": {
            "docs": "/docs" if settings.debug else "disabled",
            "health": "/health",
            "api": "/api"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with component status."""
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Database Check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "type": settings.db_type,
            "message": "Connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Redis Check (if enabled)
    if settings.redis_enabled:
        try:
            from src.cache.redis_cache import get_redis_client
            redis = get_redis_client()
            await redis.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Connection successful"
            }
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # System Metrics
    try:
        health_status["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": round(psutil.cpu_percent(interval=0.1), 2),
            "memory_percent": round(psutil.virtual_memory().percent, 2),
            "disk_percent": round(psutil.disk_usage('/').percent, 2)
        }
    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Determine overall status
    unhealthy_checks = [
        check for check in health_status["checks"].values()
        if check.get("status") == "unhealthy"
    ]
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/health/ready", tags=["Health"])
async def readiness_probe(db: Session = Depends(get_db)):
    """Kubernetes readiness probe."""
    try:
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


# =============================================================================
# METRICS ENDPOINT
# =============================================================================

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus-compatible metrics."""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics_data = f"""
# HELP api_cpu_usage_percent Current CPU usage
# TYPE api_cpu_usage_percent gauge
api_cpu_usage_percent {cpu_usage}

# HELP api_memory_usage_percent Current memory usage
# TYPE api_memory_usage_percent gauge
api_memory_usage_percent {memory.percent}

# HELP api_disk_usage_percent Current disk usage
# TYPE api_disk_usage_percent gauge
api_disk_usage_percent {disk.percent}

# HELP api_memory_available_bytes Available memory
# TYPE api_memory_available_bytes gauge
api_memory_available_bytes {memory.available}
        """.strip()
        
        return Response(content=metrics_data, media_type="text/plain")
    except Exception as e:
        return Response(
            content=f"# Error: {str(e)}",
            media_type="text/plain",
            status_code=500
        )


# =============================================================================
# PAPERS ENDPOINTS
# =============================================================================

@app.get("/api/papers", tags=["Papers"])
async def list_papers(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all papers with pagination."""
    try:
        app_logger.info(f"📋 Listing papers: skip={skip}, limit={limit}, category={category}")
        
        papers = PaperOperations.list_papers(
            db=db,
            skip=skip,
            limit=limit,
            category=category
        )
        
        total = db.query(Paper).count()
        papers_data = [serialize_paper(p) for p in papers]
        
        app_logger.info(f"✅ Found {len(papers_data)} papers (total: {total})")
        
        return {
            "papers": papers_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + len(papers_data)) < total
        }
    except Exception as e:
        app_logger.error(f"❌ Error listing papers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/papers/{arxiv_id}", tags=["Papers"])
async def get_paper(arxiv_id: str, db: Session = Depends(get_db)):
    """Get a specific paper by arXiv ID."""
    try:
        paper = PaperOperations.get_paper_by_arxiv_id(db, arxiv_id)
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return serialize_paper(paper)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"❌ Error getting paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SEARCH ENDPOINT
# =============================================================================

@app.post("/api/search", tags=["Search"])
async def search_papers(request: dict, db: Session = Depends(get_db)):
    """Search papers by keyword."""
    try:
        search_query = request.get("query", "")
        top_k = request.get("top_k", 10)
        
        if not search_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        app_logger.info(f"🔍 Searching for: '{search_query}' (top_k={top_k})")
        
        # Keyword search in title and abstract
        papers = db.query(Paper).filter(
            (Paper.title.ilike(f"%{search_query}%")) |
            (Paper.abstract.ilike(f"%{search_query}%"))
        ).limit(top_k).all()
        
        results = [serialize_paper(p) for p in papers]
        
        app_logger.info(f"✅ Found {len(results)} papers matching '{search_query}'")
        
        return {
            "query": search_query,
            "results": results,
            "total": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"❌ Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Q&A ENDPOINT
# =============================================================================

@app.post("/api/qa", tags=["Q&A"])
async def question_answer(request: dict, db: Session = Depends(get_db)):
    """Answer questions using LLM and retrieved papers."""
    try:
        question = request.get("question", "")
        top_k = request.get("top_k", 5)
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        app_logger.info(f"💬 Q&A request: {question}")
        
        # Extract keywords
        question_lower = question.lower()
        stop_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', '?']
        keywords = []
        for word in question_lower.split():
            cleaned = re.sub(r'[^\w\s]', '', word)
            if cleaned and cleaned not in stop_words and len(cleaned) > 2:
                keywords.append(cleaned)
        
        search_terms = ' '.join(keywords)
        app_logger.info(f"📝 Extracted keywords: {search_terms}")
        
        # Search papers
        papers = []
        if keywords:
            for keyword in keywords:
                results = db.query(Paper).filter(
                    (Paper.title.ilike(f"%{keyword}%")) |
                    (Paper.abstract.ilike(f"%{keyword}%"))
                ).limit(top_k).all()
                papers.extend(results)
                if len(papers) >= top_k:
                    break
        
        # Remove duplicates
        seen = set()
        unique_papers = []
        for p in papers:
            if p.id not in seen:
                seen.add(p.id)
                unique_papers.append(p)
                if len(unique_papers) >= top_k:
                    break
        
        papers = unique_papers
        
        # Fallback to recent papers
        if not papers:
            app_logger.info("No matches, using recent papers")
            papers = db.query(Paper).order_by(Paper.published_date.desc()).limit(top_k).all()
        
        app_logger.info(f"📚 Found {len(papers)} relevant papers")
        
        # Generate answer with LLM
        try:
            if settings.llm_provider == "groq" and settings.groq_api_key:
                from groq import Groq
                
                # Prepare context
                context_parts = []
                for i, p in enumerate(papers[:5], 1):
                    authors_str = ', '.join(p.authors_list) if hasattr(p, 'authors_list') else str(p.authors)
                    context_parts.append(
                        f"Paper {i}:\n"
                        f"Title: {p.title}\n"
                        f"Authors: {authors_str}\n"
                        f"Abstract: {p.abstract[:800]}...\n"
                    )
                
                context = "\n\n".join(context_parts)
                
                system_prompt = """You are an expert AI research assistant. Answer questions based on the provided research papers.
Reference specific papers when possible. Be clear about what information comes from the papers vs general knowledge."""
                
                user_prompt = f"""Research Papers Context:

{context}

Question: {question}

Please provide a comprehensive answer, citing the papers when relevant."""
                
                # Call Groq
                client = Groq(api_key=settings.groq_api_key)
                response = client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                
                answer = response.choices[0].message.content
                app_logger.info("✅ Generated answer with Groq")
                
            else:
                answer = "LLM not configured. Please set GROQ_API_KEY in environment."
                app_logger.warning("LLM not available")
        
        except Exception as e:
            app_logger.error(f"❌ LLM error: {e}")
            answer = f"Error generating answer: {str(e)}"
        
        return {
            "question": question,
            "answer": answer,
            "sources": [serialize_paper(p) for p in papers],
            "total_sources": len(papers),
            "keywords_used": search_terms
        }
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"❌ Q&A error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STATS ENDPOINT
# =============================================================================

@app.get("/api/stats", tags=["Statistics"])
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    try:
        total_papers = db.query(Paper).count()
        total_chunks = db.query(Chunk).count()
        indexed_papers = db.query(Paper).filter(Paper.indexed.isnot(None)).count()
        
        # Categories breakdown
        from sqlalchemy import func
        categories_count = db.query(
            Paper.primary_category,
            func.count(Paper.id)
        ).group_by(Paper.primary_category).all()
        
        return {
            "total_papers": total_papers,
            "indexed_papers": indexed_papers,
            "total_chunks": total_chunks,
            "categories": {cat: count for cat, count in categories_count},
            "embeddings_enabled": True,
            "llm_provider": settings.llm_provider
        }
    except Exception as e:
        app_logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    app_logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail} - "
        f"Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    app_logger.error(
        f"Unhandled exception: {str(exc)} - Path: {request.url.path}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )


# =============================================================================
# STARTUP
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
        workers=settings.api_workers if not settings.api_reload else 1
    )