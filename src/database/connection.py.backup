"""
Database connection and session management.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from src.core.config import settings
from src.core.logging_config import app_logger


# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=pool.QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.debug,  # Log SQL statements in debug mode
)


# Event listeners for connection pool monitoring
@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log database connections."""
    app_logger.debug("Database connection established")


@event.listens_for(Engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Log database disconnections."""
    app_logger.debug("Database connection closed")


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        app_logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    
    Usage:
        with get_db_context() as db:
            # Use db session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        app_logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    from src.database.models import Base
    
    try:
        app_logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        app_logger.info("✅ Database initialized successfully")
    except Exception as e:
        app_logger.error(f"❌ Failed to initialize database: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # FIXED: Added text() wrapper
        app_logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        app_logger.error(f"❌ Database connection failed: {e}")
        return False