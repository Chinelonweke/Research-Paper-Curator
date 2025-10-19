"""
FastAPI dependencies for dependency injection.
Provides reusable dependencies for routes.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.retrieval.hybrid_search import HybridSearch, get_hybrid_search
from src.llm.ollama_client import OllamaClient, get_ollama_client
from src.cache.redis_cache import RedisCache, get_redis_cache
from src.monitoring.langfuse_tracker import LangfuseTracker, get_langfuse_tracker
from src.ingestion.processor import PaperProcessor, get_paper_processor
from src.core.logging_config import app_logger


# Database dependency
def get_database() -> Session:
    """Get database session."""
    return next(get_db())


# Component dependencies
def get_search_engine() -> HybridSearch:
    """Get hybrid search engine."""
    return get_hybrid_search()


def get_llm_client() -> OllamaClient:
    """Get LLM client."""
    return get_ollama_client()


def get_cache() -> RedisCache:
    """Get cache client."""
    return get_redis_cache()


def get_tracker() -> LangfuseTracker:
    """Get monitoring tracker."""
    return get_langfuse_tracker()


def get_processor() -> PaperProcessor:
    """Get paper processor."""
    return get_paper_processor()


# Optional authentication dependency
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Get current user from authorization header.
    
    Args:
        authorization: Authorization header
    
    Returns:
        User ID or None
    """
    # Simple implementation - can be enhanced with JWT, OAuth, etc.
    if authorization:
        # Extract token/user from header
        # For now, just return a placeholder
        return "user_123"
    return None


# Rate limiting dependency (placeholder)
def check_rate_limit(user_id: Optional[str] = Depends(get_current_user)):
    """
    Check rate limit for user.
    
    Args:
        user_id: User identifier
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Placeholder for rate limiting logic
    # In production, implement with Redis or similar
    pass