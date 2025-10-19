"""
Fetch papers from arXiv API.
"""
import arxiv
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from src.core.logging_config import app_logger


class ArxivFetcher:
    """Fetch research papers from arXiv."""
    
    def __init__(self, max_results: int = 100):
        """Initialize arXiv fetcher."""
        self.max_results = max_results
        self.client = arxiv.Client()
    
    def fetch_by_category(
        self,
        category: str = "cs.AI",
        max_results: int = 50,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate
    ) -> List[Dict]:
        """
        Fetch papers by category.
        
        Args:
            category: arXiv category (e.g., cs.AI, cs.LG)
            max_results: Maximum number of papers
            sort_by: Sort criterion
            
        Returns:
            List of paper dictionaries
        """
        try:
            app_logger.info(f"Fetching {max_results} papers from category: {category}")
            
            search = arxiv.Search(
                query=f"cat:{category}",
                max_results=max_results,
                sort_by=sort_by
            )
            
            papers = []
            for result in self.client.results(search):
                paper = self._parse_result(result)
                papers.append(paper)
            
            app_logger.info(f"✅ Fetched {len(papers)} papers from {category}")
            return papers
            
        except Exception as e:
            app_logger.error(f"Error fetching papers: {e}")
            return []
    
    def fetch_by_keywords(
        self,
        keywords: List[str],
        max_results: int = 50
    ) -> List[Dict]:
        """
        Fetch papers by keywords.
        
        Args:
            keywords: List of keywords to search
            max_results: Maximum results
            
        Returns:
            List of papers
        """
        try:
            query = " OR ".join([f'"{kw}"' for kw in keywords])
            app_logger.info(f"Searching arXiv with keywords: {keywords}")
            
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in self.client.results(search):
                paper = self._parse_result(result)
                papers.append(paper)
            
            app_logger.info(f"✅ Found {len(papers)} papers")
            return papers
            
        except Exception as e:
            app_logger.error(f"Error searching papers: {e}")
            return []
    
    def fetch_recent(
        self,
        days: int = 7,
        categories: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Fetch recent papers from last N days.
        
        Args:
            days: Number of days to look back
            categories: List of categories to include
            max_results: Maximum results
            
        Returns:
            List of recent papers
        """
        if categories is None:
            categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
        
        all_papers = []
        per_category = max_results // len(categories)
        
        for category in categories:
            papers = self.fetch_by_category(
                category=category,
                max_results=per_category,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            all_papers.extend(papers)
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_papers = [
            p for p in all_papers
            if p['published_date'] and p['published_date'] > cutoff_date
        ]
        
        app_logger.info(f"✅ Found {len(recent_papers)} recent papers from last {days} days")
        return recent_papers[:max_results]
    
    def _parse_result(self, result: arxiv.Result) -> Dict:
        """Parse arXiv result into dictionary."""
        return {
            'arxiv_id': result.entry_id.split('/')[-1],
            'title': result.title,
            'abstract': result.summary,
            'authors': [author.name for author in result.authors],
            'categories': result.categories,
            'primary_category': result.primary_category,
            'published_date': result.published,
            'updated_date': result.updated,
            'pdf_url': result.pdf_url,
            'comment': result.comment,
            'journal_ref': result.journal_ref,
            'doi': result.doi,
        }


def fetch_papers_batch(
    categories: List[str] = None,
    max_per_category: int = 50
) -> List[Dict]:
    """
    Convenience function to fetch papers in batch.
    
    Args:
        categories: List of arXiv categories
        max_per_category: Max papers per category
        
    Returns:
        List of papers
    """
    if categories is None:
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE"]
    
    fetcher = ArxivFetcher()
    all_papers = []
    
    for category in categories:
        papers = fetcher.fetch_by_category(category, max_per_category)
        all_papers.extend(papers)
    
    # Remove duplicates by arxiv_id
    seen = set()
    unique_papers = []
    for paper in all_papers:
        if paper['arxiv_id'] not in seen:
            seen.add(paper['arxiv_id'])
            unique_papers.append(paper)
    
    app_logger.info(f"✅ Total unique papers fetched: {len(unique_papers)}")
    return unique_papers