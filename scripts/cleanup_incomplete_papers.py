"""
Delete papers that don't have chunks (incomplete ingestion).
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models import Paper, Chunk
from sqlalchemy import func

print("="*60)
print("CLEANUP: Delete Incomplete Papers")
print("="*60)

db = next(get_db())

try:
    # Find papers without chunks (failed ingestions)
    papers_without_chunks = (
        db.query(Paper)
        .outerjoin(Chunk)
        .group_by(Paper.id)
        .having(func.count(Chunk.id) == 0)
        .all()
    )
    
    print(f"\nFound {len(papers_without_chunks)} papers without chunks:")
    for paper in papers_without_chunks:
        print(f"  - {paper.arxiv_id}: {paper.title[:50]}...")
    
    if papers_without_chunks:
        print(f"\n⚠️  These {len(papers_without_chunks)} papers will be DELETED")
        print("(They have no content/chunks - failed ingestion)")
        confirm = input("\nType 'DELETE' to confirm: ")
        
        if confirm == 'DELETE':
            for paper in papers_without_chunks:
                print(f"Deleting {paper.arxiv_id}...")
                db.delete(paper)
            db.commit()
            print(f"\n✅ Deleted {len(papers_without_chunks)} incomplete papers")
        else:
            print("\n❌ Cancelled - no papers deleted")
    else:
        print("\n✅ No incomplete papers found! Database is clean.")
    
    print("="*60)
    
finally:
    db.close()