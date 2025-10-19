"""Test arXiv paper fetching."""
import arxiv

print("=" * 60)
print("📚 TESTING ARXIV CONNECTION")
print("=" * 60)

print("\n1️⃣ Fetching papers about 'large language models'...")
print("   (Getting 3 papers as a test)")

try:
    # Search arXiv
    search = arxiv.Search(
        query="large language models",
        max_results=3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    papers = list(search.results())
    
    print(f"\n✅ Found {len(papers)} papers!")
    print("\n" + "=" * 60)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n📄 Paper {i}:")
        print(f"   Title: {paper.title}")
        print(f"   Authors: {', '.join([a.name for a in paper.authors[:3]])}")
        print(f"   Published: {paper.published.date()}")
        print(f"   ArXiv ID: {paper.entry_id.split('/')[-1]}")
        print(f"   Abstract: {paper.summary[:200]}...")
    
    print("\n" + "=" * 60)
    print("🎉 ARXIV CONNECTION WORKING!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTrying to install arxiv package...")
    import subprocess
    subprocess.run(["pip", "install", "arxiv"])
    print("Please run this script again!")