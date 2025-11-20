"""
Database Connection - NeonDB
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import logging
import os

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "postgresql://neondb_owner:npg_zqua53pIJGUP@ep-frosty-queen-ahy6nn7k-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connected")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False