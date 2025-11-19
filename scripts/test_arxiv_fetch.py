"""
Debug script to test arXiv fetching.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.arxiv_fetcher import ArxivFetcher
import json


def test_fetch():
    """Test fetching a single paper."""
    print("Testing arXiv fetching...\n")
    
    fetcher = ArxivFetcher()
    
    # Fetch just 2 papers for testing
    papers = fetcher.fetch_by_category("cs.AI", max_results=2)
    
    print(f"Fetched {len(papers)} papers\n")
    
    if papers:
        paper = papers[0]
        print("=" * 60)
        print("FIRST PAPER STRUCTURE:")
        print("=" * 60)
        print(f"Type: {type(paper)}")
        print(f"Keys: {paper.keys() if isinstance(paper, dict) else 'Not a dict!'}")
        print("\nFull paper data:")
        print(json.dumps(paper, indent=2, default=str))
        print("=" * 60)
    else:
        print("❌ No papers fetched!")


if __name__ == "__main__":
    test_fetch()