"""
Database migration script - Fixes schema and adds embedding column.
This version handles schema mismatches and recreates tables if needed.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from src.database.connection import engine
from src.database.models import Base
from src.core.logging_config import app_logger


def check_schema_issues():
    """Check if database has schema issues."""
    try:
        inspector = inspect(engine)
        
        # Check if chunks table exists and has correct columns
        if 'chunks' in inspector.get_table_names():
            chunks_cols = {col['name'] for col in inspector.get_columns('chunks')}
            if 'text' not in chunks_cols:
                return True, "chunks table missing 'text' column"
        
        # Check if papers table has correct column types
        if 'papers' in inspector.get_table_names():
            papers_cols = inspector.get_columns('papers')
            for col in papers_cols:
                if col['name'] in ['authors', 'categories']:
                    col_type = str(col['type']).lower()
                    if 'array' in col_type or '[]' in col_type:
                        return True, f"papers.{col['name']} is ARRAY type (should be TEXT)"
        
        return False, None
    except Exception as e:
        app_logger.error(f"Error checking schema: {e}")
        return True, str(e)


def recreate_database():
    """Recreate database with correct schema."""
    print("\n⚠️  Recreating database with correct schema...")
    print("This will DELETE all existing data!")
    
    confirm = input("\nType 'YES' to continue: ")
    if confirm != 'YES':
        print("❌ Cancelled")
        return False
    
    try:
        print("\n1. Dropping all tables...")
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS chunks CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS search_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS system_metrics CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS papers CASCADE"))
        print("✅ Tables dropped")
        
        print("\n2. Creating tables with correct schema...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")
        
        print("\n3. Verifying schema...")
        inspector = inspect(engine)
        
        # Check papers columns
        papers_cols = inspector.get_columns('papers')
        print("\nPapers table:")
        for col in papers_cols:
            if col['name'] in ['authors', 'categories', 'embedding']:
                print(f"  ✓ {col['name']}: {col['type']}")
        
        # Check chunks columns
        chunks_cols = inspector.get_columns('chunks')
        print("\nChunks table:")
        for col in chunks_cols:
            if col['name'] in ['text', 'embedding']:
                print(f"  ✓ {col['name']}: {col['type']}")
        
        return True
        
    except Exception as e:
        app_logger.error(f"Recreation failed: {e}")
        print(f"❌ Error: {e}")
        return False


def add_embedding_column_only():
    """Just add embedding column if it's missing."""
    try:
        inspector = inspect(engine)
        chunks_cols = {col['name'] for col in inspector.get_columns('chunks')}
        
        if 'embedding' not in chunks_cols:
            print("Adding embedding column to chunks table...")
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE chunks ADD COLUMN embedding TEXT"))
            print("✅ Embedding column added")
            return True
        else:
            print("✅ Embedding column already exists")
            return True
            
    except Exception as e:
        app_logger.error(f"Error adding embedding column: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Schema Fix & Embedding Column")
    print("=" * 60)
    
    # Check for schema issues
    has_issues, issue_desc = check_schema_issues()
    
    if has_issues:
        print(f"\n⚠️  SCHEMA ISSUE DETECTED:")
        print(f"   {issue_desc}")
        print("\n" + "="*60)
        print("RECOMMENDED: Recreate database with correct schema")
        print("="*60)
        
        if recreate_database():
            print("\n" + "="*60)
            print("✅ SUCCESS! Database recreated with correct schema")
            print("="*60)
            print("\nYou can now ingest papers:")
            print("  python scripts/ingest_papers.py --max-per-category 50")
            print("="*60)
        else:
            print("\n❌ Migration failed")
    else:
        print("\n✅ Schema looks good!")
        if add_embedding_column_only():
            print("\n" + "="*60)
            print("✅ SUCCESS! Database is ready")
            print("="*60)