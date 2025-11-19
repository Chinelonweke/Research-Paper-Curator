"""
Initialize database tables
"""
from src.database.models import Base
from src.database.connection import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Create all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Tables created successfully!")
    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    init_db()
