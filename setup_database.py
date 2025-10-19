"""Create database tables for papers."""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from src.core.config import settings

print("=" * 60)
print("💾 SETTING UP DATABASE TABLES")
print("=" * 60)

# Create engine
engine = create_engine(settings.database_url, echo=False)
Base = declarative_base()

# Define Paper table
class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(Text)  # JSON string
    abstract = Column(Text)
    published_date = Column(DateTime)
    pdf_url = Column(String(500))
    categories = Column(String(200))
    full_text = Column(Text)  # Extracted PDF text
    created_at = Column(DateTime, default=datetime.utcnow)

# Define Chunk table (for RAG)
class Chunk(Base):
    __tablename__ = 'chunks'
    
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, nullable=False)  # Foreign key to papers
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer)  # Position in paper
    embedding = Column(Text)  # JSON string of vector
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
print("\n1️⃣ Creating tables...")
try:
    Base.metadata.create_all(engine)
    print("   ✅ Tables created!")
    
    # List tables
    print("\n2️⃣ Tables in database:")
    for table in Base.metadata.tables.keys():
        print(f"   📋 {table}")
    
    # Test insert
    print("\n3️⃣ Testing database operations...")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if we can query
    paper_count = session.query(Paper).count()
    chunk_count = session.query(Chunk).count()
    
    print(f"   📄 Papers in database: {paper_count}")
    print(f"   📝 Chunks in database: {chunk_count}")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("🎉 DATABASE READY FOR PAPERS!")
    print("=" * 60)
    print(f"\n📁 Database file: {settings.database_url}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()