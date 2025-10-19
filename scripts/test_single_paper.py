"""
Test ingesting a single paper to see exact error.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.arxiv_fetcher import ArxivFetcher
from src.database.connection import get_db
from src.ingestion.processor import PaperProcessor
from src.core.logging_config import app_logger

print("="*60)
print("TEST: Ingest Single Paper")
print("="*60)

# Fetch ONE paper
fetcher = ArxivFetcher()
print("\nFetching 1 paper from cs.AI...")
papers = fetcher.fetch_by_category('cs.AI', max_results=1)

if not papers:
    print("❌ No papers fetched!")
    sys.exit(1)

paper = papers[0]
print(f"\nPaper fetched: {paper['arxiv_id']}")
print(f"Title: {paper['title'][:60]}...")
print(f"Authors type: {type(paper['authors'])}")
print(f"Authors value: {paper['authors']}")

# Test string conversion
authors = paper['authors']
if isinstance(authors, list):
    authors_str = ', '.join(authors)
    print(f"\nConverted authors: '{authors_str}'")
    print(f"Type: {type(authors_str)}")
    print(f"Starts with '[': {authors_str.startswith('[')}")
else:
    print(f"\nAuthors already string: '{authors}'")

# Try to ingest
print("\n" + "="*60)
print("Attempting ingestion...")
print("="*60)

db = next(get_db())
try:
    processor = PaperProcessor(db)
    result = processor.process_paper(paper)
    
    if result:
        print(f"\n✅ SUCCESS! Paper {result.arxiv_id} ingested")
        print(f"Paper ID: {result.id}")
        print(f"Authors stored as: {result.authors}")
        print(f"Authors list: {result.authors_list}")
    else:
        print("\n❌ FAILED! Check logs above")
        
finally:
    db.close()

print("="*60)