"""
Database setup script.
Initializes database schema and optionally seeds sample data.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import init_db, check_db_connection, engine
from src.database.models import Base
from src.core.config import settings
from src.core.logging_config import app_logger


def setup_database(recreate: bool = False):
    """
    Setup database.
    
    Args:
        recreate: If True, drop all tables and recreate
    """
    try:
        app_logger.info("=" * 60)
        app_logger.info("DATABASE SETUP")
        app_logger.info("=" * 60)
        
        # Check connection
        app_logger.info("Checking database connection...")
        if not check_db_connection():
            app_logger.error("Cannot connect to database. Please check your configuration.")
            return False
        
        # Recreate if requested
        if recreate:
            app_logger.warning("DROPPING ALL TABLES...")
            response = input("Are you sure you want to drop all tables? (yes/no): ")
            if response.lower() == 'yes':
                Base.metadata.drop_all(bind=engine)
                app_logger.info("All tables dropped")
            else:
                app_logger.info("Aborted")
                return False
        
        # Create tables
        app_logger.info("Creating database tables...")
        init_db()
        
        app_logger.info("=" * 60)
        app_logger.info("✓ DATABASE SETUP COMPLETE")
        app_logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        app_logger.error(f"Database setup failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup database for RAG system")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop all tables and recreate (WARNING: destroys all data)"
    )
    
    args = parser.parse_args()
    
    success = setup_database(recreate=args.recreate)
    
    if success:
        print("\n✓ Database setup successful!")
        print("\nNext steps:")
        print("1. Seed sample data: python scripts/seed_data.py")
        print("2. Start the API: python -m src.api.main")
    else:
        print("\n✗ Database setup failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()