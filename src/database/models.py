"""
Database Models - WITH USER TRACKING AND RAG SUPPORT
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

Base = declarative_base()

class User(Base):
    """User model for authentication and tracking"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    searches = relationship("SearchLog", back_populates="user")
    saved_papers = relationship("SavedPaper", back_populates="user")

class SearchLog(Base):
    """Track all searches for analytics"""
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query = Column(String(500), nullable=False)
    results_count = Column(Integer)
    search_type = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    user = relationship("User", back_populates="searches")

class SavedPaper(Base):
    """User's bookmarked papers"""
    __tablename__ = "saved_papers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    user = relationship("User", back_populates="saved_papers")
    paper = relationship("Paper")

class Paper(Base):
    """Research paper model"""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    arxiv_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    authors = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    pdf_url = Column(String(500))
    published_date = Column(DateTime, index=True)
    primary_category = Column(String(50))
    categories = Column(String(200))
    indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to chunks
    chunks = relationship("PaperChunk", back_populates="paper", cascade="all, delete-orphan")


class PaperChunk(Base):
    """Paper chunks with vector embeddings for RAG"""
    __tablename__ = "paper_chunks"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(384)) if PGVECTOR_AVAILABLE else Column(Text)  # 384-dim for all-MiniLM-L6-v2
    start_char = Column(Integer)
    end_char = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to paper
    paper = relationship("Paper", back_populates="chunks")
 