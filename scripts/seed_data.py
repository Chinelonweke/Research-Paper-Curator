"""
Seed sample data into the database.
Fetches a few papers from arXiv for testing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.processor import get_paper_processor
from src.core.config import settings
from src.core.logging_config import app_logger


def seed_data():
    """Seed sample data."""
    try:
        app_logger.info("=" * 60)
        app_logger.info("SEEDING SAMPLE DATA")
        app_logger.info("=" * 60)

        # Fetch and process sample papers
        app_logger.info("Fetching sample papers from arXiv...")
        processor = get_paper_processor()

        # Process recent papers
        stats = processor.process_recent_papers(
            days_back=7,
            max_results=10
        )

        app_logger.info(f"Processing complete: {stats}")
        
        # Get stats
        system_stats = processor.get_processing_stats()
        app_logger.info(f"System stats: {system_stats}")

        app_logger.info("=" * 60)
        app_logger.info("✅ SEEDING COMPLETE")
        app_logger.info("=" * 60)

        return True

    except Exception as e:
        app_logger.error(f"Seeding failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    success = seed_data()
    
    if success:
        print("\n✅ Data seeding successful!")
        print("\nYou can now:")
        print("1. Start the API: python -m src.api.main")
        print("2. Start the UI: python -m src.ui.gradio_interface")
        print("3. Test the system with real data!")
    else:
        print("\n❌ Data seeding failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()