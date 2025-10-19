"""
Database sharding implementation for horizontal scaling.
Distributes data across multiple database instances.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import hashlib
from src.core.config import settings
from src.core.logging_config import app_logger


class ShardManager:
    """
    Manages database sharding across multiple PostgreSQL instances.
    
    Sharding Strategy: Hash-based on paper_id
    - Shard 0: paper_id % 4 == 0
    - Shard 1: paper_id % 4 == 1
    - Shard 2: paper_id % 4 == 2
    - Shard 3: paper_id % 4 == 3
    """
    
    def __init__(self, shard_count: int = 4):
        self.shard_count = shard_count
        self.shards = {}
        self.session_makers = {}
        
        self._initialize_shards()
    
    def _initialize_shards(self):
        """Initialize connections to all shards."""
        for shard_id in range(self.shard_count):
            shard_url = self._get_shard_url(shard_id)
            
            engine = create_engine(
                shard_url,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False
            )
            
            self.shards[shard_id] = engine
            self.session_makers[shard_id] = sessionmaker(bind=engine)
            
            app_logger.info(f"✅ Initialized shard {shard_id}: {shard_url}")
    
    def _get_shard_url(self, shard_id: int) -> str:
        """
        Get database URL for a specific shard.
        
        In production, each shard should be on a separate server:
        - Shard 0: db1.yourdomain.com
        - Shard 1: db2.yourdomain.com
        - Shard 2: db3.yourdomain.com
        - Shard 3: db4.yourdomain.com
        """
        # For single server (development)
        if self.shard_count == 1:
            return settings.database_url
        
        # For multiple servers (production)
        shard_hosts = {
            0: "db1.yourdomain.com",
            1: "db2.yourdomain.com",
            2: "db3.yourdomain.com",
            3: "db4.yourdomain.com"
        }
        
        host = shard_hosts.get(shard_id, settings.db_host)
        
        return (
            f"postgresql://{settings.db_user}:{settings.db_password}"
            f"@{host}:{settings.db_port}/research_papers_shard_{shard_id}"
        )
    
    def get_shard_for_paper(self, paper_id: int) -> int:
        """
        Determine which shard contains this paper.
        
        Args:
            paper_id: Paper ID
        
        Returns:
            Shard ID (0 to shard_count-1)
        """
        return paper_id % self.shard_count
    
    def get_shard_for_arxiv_id(self, arxiv_id: str) -> int:
        """
        Determine shard based on arXiv ID (for new papers).
        
        Args:
            arxiv_id: arXiv ID
        
        Returns:
            Shard ID
        """
        # Hash arxiv_id to determine shard
        hash_value = int(hashlib.md5(arxiv_id.encode()).hexdigest(), 16)
        return hash_value % self.shard_count
    
    def get_session(self, shard_id: int) -> Session:
        """
        Get database session for a specific shard.
        
        Args:
            shard_id: Shard ID
        
        Returns:
            SQLAlchemy session
        """
        if shard_id not in self.session_makers:
            raise ValueError(f"Invalid shard_id: {shard_id}")
        
        return self.session_makers[shard_id]()
    
    def get_all_sessions(self) -> List[Session]:
        """Get sessions for all shards (for cross-shard queries)."""
        return [self.session_makers[i]() for i in range(self.shard_count)]
    
    def execute_on_all_shards(self, func, *args, **kwargs) -> List[Any]:
        """
        Execute a function on all shards and aggregate results.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
        
        Returns:
            List of results from all shards
        """
        results = []
        
        for shard_id in range(self.shard_count):
            session = self.get_session(shard_id)
            try:
                result = func(session, *args, **kwargs)
                results.append(result)
            finally:
                session.close()
        
        return results
    
    def migrate_shard(self, from_shard: int, to_shard: int, paper_ids: List[int]):
        """
        Migrate papers between shards (for rebalancing).
        
        Args:
            from_shard: Source shard ID
            to_shard: Destination shard ID
            paper_ids: List of paper IDs to migrate
        """
        from src.database.models import Paper, Chunk
        
        source_session = self.get_session(from_shard)
        dest_session = self.get_session(to_shard)
        
        try:
            for paper_id in paper_ids:
                # Fetch paper and chunks from source
                paper = source_session.query(Paper).filter(Paper.id == paper_id).first()
                
                if not paper:
                    continue
                
                chunks = source_session.query(Chunk).filter(Chunk.paper_id == paper_id).all()
                
                # Copy to destination
                source_session.expunge(paper)
                dest_session.add(paper)
                
                for chunk in chunks:
                    source_session.expunge(chunk)
                    dest_session.add(chunk)
                
                dest_session.commit()
                
                # Delete from source
                source_session.query(Chunk).filter(Chunk.paper_id == paper_id).delete()
                source_session.query(Paper).filter(Paper.id == paper_id).delete()
                source_session.commit()
                
                app_logger.info(f"Migrated paper {paper_id} from shard {from_shard} to {to_shard}")
        
        except Exception as e:
            source_session.rollback()
            dest_session.rollback()
            app_logger.error(f"Error migrating paper: {e}")
            raise
        
        finally:
            source_session.close()
            dest_session.close()
    
    def get_shard_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for all shards."""
        from src.database.models import Paper, Chunk
        
        stats = {}
        
        for shard_id in range(self.shard_count):
            session = self.get_session(shard_id)
            
            try:
                paper_count = session.query(Paper).count()
                chunk_count = session.query(Chunk).count()
                
                stats[shard_id] = {
                    "papers": paper_count,
                    "chunks": chunk_count,
                    "url": self._get_shard_url(shard_id)
                }
            
            finally:
                session.close()
        
        return stats


# Global shard manager
_shard_manager: Optional[ShardManager] = None


def get_shard_manager() -> ShardManager:
    """Get global shard manager instance."""
    global _shard_manager
    if _shard_manager is None:
        shard_count = getattr(settings, 'shard_count', 4)
        _shard_manager = ShardManager(shard_count=shard_count)
    return _shard_manager


class ShardedPaperOperations:
    """Paper operations that work across shards."""
    
    def __init__(self):
        self.shard_manager = get_shard_manager()
    
    def create_paper(self, paper_data: Dict[str, Any]) -> int:
        """Create paper in appropriate shard."""
        arxiv_id = paper_data['arxiv_id']
        shard_id = self.shard_manager.get_shard_for_arxiv_id(arxiv_id)
        
        session = self.shard_manager.get_session(shard_id)
        
        try:
            from src.database.models import Paper
            paper = Paper(**paper_data)
            session.add(paper)
            session.commit()
            session.refresh(paper)
            
            app_logger.info(f"Created paper {arxiv_id} in shard {shard_id}")
            return paper.id
        
        finally:
            session.close()
    
    def get_paper_by_id(self, paper_id: int):
        """Get paper from its shard."""
        shard_id = self.shard_manager.get_shard_for_paper(paper_id)
        session = self.shard_manager.get_session(shard_id)
        
        try:
            from src.database.models import Paper
            return session.query(Paper).filter(Paper.id == paper_id).first()
        finally:
            session.close()
    
    def search_papers(self, query: Dict[str, Any]) -> List:
        """Search papers across all shards."""
        def search_in_shard(session, query):
            from src.database.models import Paper
            q = session.query(Paper)
            
            # Apply filters
            if 'category' in query:
                q = q.filter(Paper.categories.contains([query['category']]))
            
            return q.limit(query.get('limit', 20)).all()
        
        # Execute on all shards
        all_results = self.shard_manager.execute_on_all_shards(search_in_shard, query)
        
        # Flatten and sort
        papers = []
        for shard_results in all_results:
            papers.extend(shard_results)
        
        # Sort by published date
        papers.sort(key=lambda p: p.published_date, reverse=True)
        
        return papers[:query.get('limit', 20)]