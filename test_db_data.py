"""Quick test to see data in database."""
from src.database.connection import get_db_context
from src.database.models import Paper

with get_db_context() as db:
    count = db.query(Paper).count()
    papers = db.query(Paper).limit(3).all()
    
    print(f"\n✅ Papers in database: {count}\n")
    
    if papers:
        for p in papers:
            print(f"📄 {p.arxiv_id}")
            print(f"   Title: {p.title[:70]}...")
            print(f"   Authors: {len(p.authors)} authors")
            print(f"   Categories: {p.categories}")
            print()
    else:
        print("❌ No papers found!\n")