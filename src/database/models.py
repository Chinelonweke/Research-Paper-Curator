"""
Database models for papers and chunks.
FIXED: Handles both JSON and comma-separated string storage for PostgreSQL compatibility.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()


# ==========================================================
# 📄 Paper Model
# ==========================================================
class Paper(Base):
    """Paper model representing an arXiv paper."""
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    arxiv_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=False)
    authors = Column(Text, nullable=False)  # Comma-separated string
    categories = Column(Text, nullable=False)  # Comma-separated string
    primary_category = Column(String(50))
    published_date = Column(DateTime)
    updated_date = Column(DateTime)
    pdf_url = Column(String(500))
    comment = Column(Text)
    journal_ref = Column(String(500))
    doi = Column(String(200))
    indexed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunks = relationship("Chunk", back_populates="paper", cascade="all, delete-orphan")
    
    @property
    def authors_list(self):
        """Get authors as list - handles both JSON and comma-separated formats."""
        try:
            if isinstance(self.authors, str):
                # Try JSON first (for backward compatibility with existing data)
                if self.authors.startswith('['):
                    return json.loads(self.authors)
                # Otherwise split by comma (new format)
                return [a.strip() for a in self.authors.split(',') if a.strip()]
            return self.authors if isinstance(self.authors, list) else []
        except:
            return []
    
    @property
    def categories_list(self):
        """Get categories as list - handles both JSON and comma-separated formats."""
        try:
            if isinstance(self.categories, str):
                # Try JSON first (for backward compatibility)
                if self.categories.startswith('['):
                    return json.loads(self.categories)
                # Otherwise split by comma (new format)
                return [c.strip() for c in self.categories.split(',') if c.strip()]
            return self.categories if isinstance(self.categories, list) else []
        except:
            return []
    
    def __repr__(self):
        return f"<Paper(arxiv_id='{self.arxiv_id}', title='{self.title[:50]}...')>"


# ==========================================================
# 📝 Chunk Model - WITH EMBEDDING COLUMN
# ==========================================================
class Chunk(Base):
    """Chunk model representing a text chunk from a paper."""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    
    # ⭐ EMBEDDING COLUMN - Store as JSON string
    embedding = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    paper = relationship("Paper", back_populates="chunks")
    
    @property
    def embedding_vector(self):
        """Get embedding as list/array."""
        if not self.embedding:
            return None
        try:
            if isinstance(self.embedding, str):
                return json.loads(self.embedding)
            return self.embedding
        except:
            return None
    
    def set_embedding(self, vector):
        """Set embedding from numpy array or list."""
        if vector is not None:
            import numpy as np
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            self.embedding = json.dumps(vector)
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, paper_id={self.paper_id}, chunk_index={self.chunk_index})>"


# ==========================================================
# 🔍 SearchLog Model
# ==========================================================
class SearchLog(Base):
    """Search query logging for analytics."""
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    top_k = Column(Integer, default=5)
    search_type = Column(String(50), default="hybrid")
    num_results = Column(Integer)
    processing_time_ms = Column(Float)
    cache_hit = Column(Integer, default=0)
    user_id = Column(String(100))
    session_id = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<SearchLog(query='{self.query[:50]}...', timestamp='{self.timestamp}')>"


# ==========================================================
# ⚙️ SystemMetrics Model
# ==========================================================
class SystemMetrics(Base):
    """System health and performance metrics."""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_metrics_type_time", "metric_type", "timestamp"),
    )
    
    def __repr__(self):
        return f"<SystemMetrics(type='{self.metric_type}', value={self.metric_value})>"