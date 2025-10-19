"""
Script to ingest papers from arXiv with embeddings.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.database.connection import get_db, engine
from src.database.models import Base
from src.ingestion.processor import PaperProcessor
from src.core.logging_config import app_logger


def ingest_papers(categories=None, max_per_category=50):
    """Ingest papers from arXiv."""
    if categories is None:
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
    
    print("=" * 60)
    print("ARXIV PAPER INGESTION")
    print("=" * 60)
    print(f"Categories: {categories}")
    print(f"Max per category: {max_per_category}")
    print("=" * 60)
    print()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Get DB session
    db = next(get_db())
    
    try:
        processor = PaperProcessor(db)
        total = processor.ingest_from_arxiv(categories, max_per_category)
        
        print()
        print("=" * 60)
        if total > 0:
            print(f"✅ SUCCESS! Ingested {total} papers with embeddings")
            print("=" * 60)
            print("\n🎉 You can now:")
            print("  - Start API: python -m src.api.main")
            print("  - Start UI: python -m src.ui.gradio_interface")
            print("  - Use semantic search!")
        else:
            print("⚠️ No papers were ingested")
            print("=" * 60)
        return total
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {str(e)}")
        print("=" * 60)
        app_logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest papers from arXiv")
    parser.add_argument("--categories", nargs="+", default=["cs.AI", "cs.LG", "cs.CL", "cs.CV"])
    parser.add_argument("--max-per-category", type=int, default=50)
    
    args = parser.parse_args()
    
    print("\n🚀 Starting paper ingestion with embeddings...")
    print(f"📚 Categories: {args.categories}")
    print(f"📊 Max per category: {args.max_per_category}")
    print(f"⏱️  This will take 15-30 minutes...\n")
    
    total = ingest_papers(args.categories, args.max_per_category)
    
    sys.exit(0 if total > 0 else 1)