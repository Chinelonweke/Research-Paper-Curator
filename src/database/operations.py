"""
Database CRUD operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from src.database.models import Paper, Chunk, SearchLog, SystemMetrics
from src.core.logging_config import app_logger


class PaperOperations:
    """CRUD operations for papers."""
    
    @staticmethod
    def create_paper(db: Session, paper_data: Dict[str, Any]) -> Paper:
        """
        Create a new paper.
        
        Args:
            db: Database session
            paper_data: Paper data dictionary
        
        Returns:
            Created Paper object
        """
        try:
            paper = Paper(**paper_data)
            db.add(paper)
            db.commit()
            db.refresh(paper)
            app_logger.info(f"Created paper: {paper.arxiv_id}")
            return paper
        except Exception as e:
            db.rollback()
            app_logger.error(f"Error creating paper: {e}")
            raise
    
    @staticmethod
    def get_paper_by_arxiv_id(db: Session, arxiv_id: str) -> Optional[Paper]:
        """Get paper by arXiv ID."""
        return db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
    
    @staticmethod
    def get_paper_by_id(db: Session, paper_id: int) -> Optional[Paper]:
        """Get paper by internal ID."""
        return db.query(Paper).filter(Paper.id == paper_id).first()
    
    @staticmethod
    def list_papers(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Paper]:
        """
        List papers with optional filters.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by category
            start_date: Filter by published date (from)
            end_date: Filter by published date (to)
        
        Returns:
            List of Paper objects
        """
        query = db.query(Paper)
        
        if category:
            query = query.filter(Paper.categories.contains([category]))
        
        if start_date:
            query = query.filter(Paper.published_date >= start_date)
        
        if end_date:
            query = query.filter(Paper.published_date <= end_date)
        
        return query.order_by(desc(Paper.published_date)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_paper(db: Session, paper_id: int, update_data: Dict[str, Any]) -> Optional[Paper]:
        """Update paper."""
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if paper:
            for key, value in update_data.items():
                setattr(paper, key, value)
            paper.last_updated = datetime.utcnow()
            db.commit()
            db.refresh(paper)
            app_logger.info(f"Updated paper: {paper.arxiv_id}")
        return paper
    
    @staticmethod
    def delete_paper(db: Session, paper_id: int) -> bool:
        """Delete paper."""
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if paper:
            db.delete(paper)
            db.commit()
            app_logger.info(f"Deleted paper: {paper.arxiv_id}")
            return True
        return False
    
    @staticmethod
    def paper_exists(db: Session, arxiv_id: str) -> bool:
        """Check if paper exists."""
        return db.query(Paper).filter(Paper.arxiv_id == arxiv_id).count() > 0


class ChunkOperations:
    """CRUD operations for chunks."""
    
    @staticmethod
    def create_chunks(db: Session, paper_id: int, chunks_data: List[Dict[str, Any]]) -> List[Chunk]:
        """Create multiple chunks for a paper."""
        try:
            chunks = []
            for chunk_data in chunks_data:
                chunk = Chunk(paper_id=paper_id, **chunk_data)
                chunks.append(chunk)
            
            db.add_all(chunks)
            db.commit()
            
            for chunk in chunks:
                db.refresh(chunk)
            
            app_logger.info(f"Created {len(chunks)} chunks for paper_id: {paper_id}")
            return chunks
        except Exception as e:
            db.rollback()
            app_logger.error(f"Error creating chunks: {e}")
            raise
    
    @staticmethod
    def get_chunks_by_paper(db: Session, paper_id: int) -> List[Chunk]:
        """Get all chunks for a paper."""
        return db.query(Chunk).filter(Chunk.paper_id == paper_id).order_by(Chunk.chunk_index).all()
    
    @staticmethod
    def get_chunk_by_id(db: Session, chunk_id: int) -> Optional[Chunk]:
        """Get chunk by ID."""
        return db.query(Chunk).filter(Chunk.id == chunk_id).first()


class SearchLogOperations:
    """Operations for search logging."""
    
    @staticmethod
    def log_search(db: Session, log_data: Dict[str, Any]) -> SearchLog:
        """Log a search query."""
        try:
            search_log = SearchLog(**log_data)
            db.add(search_log)
            db.commit()
            db.refresh(search_log)
            return search_log
        except Exception as e:
            db.rollback()
            app_logger.error(f"Error logging search: {e}")
            raise
    
    @staticmethod
    def get_recent_searches(db: Session, limit: int = 100) -> List[SearchLog]:
        """Get recent search logs."""
        return db.query(SearchLog).order_by(desc(SearchLog.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_popular_queries(db: Session, limit: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """Get most popular search queries."""
        from sqlalchemy import func
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            SearchLog.query,
            func.count(SearchLog.id).label('count')
        ).filter(
            SearchLog.timestamp >= cutoff_date
        ).group_by(
            SearchLog.query
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [{"query": r[0], "count": r[1]} for r in results]


class MetricsOperations:
    """Operations for system metrics."""
    
    @staticmethod
    def record_metric(db: Session, metric_type: str, metric_value: float, metadata: Optional[Dict] = None):
        """Record a system metric."""
        try:
            metric = SystemMetrics(
                metric_type=metric_type,
                metric_value=metric_value,
                metadata=metadata
            )
            db.add(metric)
            db.commit()
        except Exception as e:
            db.rollback()
            app_logger.error(f"Error recording metric: {e}")