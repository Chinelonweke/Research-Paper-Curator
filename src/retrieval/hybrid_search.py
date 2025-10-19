"""
Hybrid search combining vector and keyword search.
Uses Reciprocal Rank Fusion (RRF) to merge results.
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
from src.retrieval.opensearch_client import OpenSearchClient, get_opensearch_client
from src.embeddings.generator import EmbeddingGenerator, get_embedding_generator
from src.core.config import settings
from src.core.logging_config import app_logger


class HybridSearch:
    """
    Hybrid search combining vector and keyword search.
    
    Features:
    - Vector similarity search (semantic)
    - BM25 keyword search (lexical)
    - Reciprocal Rank Fusion (RRF) for result merging
    - Configurable alpha parameter for weighting
    """
    
    def __init__(
        self,
        opensearch_client: Optional[OpenSearchClient] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        """
        Initialize hybrid search.
        
        Args:
            opensearch_client: OpenSearch client instance
            embedding_generator: Embedding generator instance
        """
        self.os_client = opensearch_client or get_opensearch_client()
        self.embedding_gen = embedding_generator or get_embedding_generator()
        self.alpha = settings.hybrid_search_alpha  # Weight for vector vs keyword
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: Optional[float] = None,
        filter_categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            alpha: Weight for vector search (0-1), keyword search gets (1-alpha)
            filter_categories: Filter results by paper categories
        
        Returns:
            List of merged and ranked results
        """
        try:
            app_logger.info(f"Hybrid search: '{query}' (top_k={top_k})")
            
            alpha = alpha if alpha is not None else self.alpha
            
            # Prepare filter
            filter_query = None
            if filter_categories:
                filter_query = {
                    "terms": {"paper_categories": filter_categories}
                }
            
            # 1. Vector search
            app_logger.debug("Performing vector search...")
            query_embedding = self.embedding_gen.generate_embedding(query)
            vector_results = self.os_client.vector_search(
                query_vector=query_embedding.tolist(),
                top_k=top_k * 2,  # Retrieve more for fusion
                filter_query=filter_query
            )
            
            # 2. Keyword search
            app_logger.debug("Performing keyword search...")
            keyword_results = self.os_client.keyword_search(
                query_text=query,
                top_k=top_k * 2,
                filter_query=filter_query
            )
            
            # 3. Merge using RRF
            app_logger.debug("Merging results with RRF...")
            merged_results = self._reciprocal_rank_fusion(
                vector_results=vector_results,
                keyword_results=keyword_results,
                alpha=alpha,
                k=60  # RRF parameter
            )
            
            # 4. Return top_k results
            final_results = merged_results[:top_k]
            
            app_logger.info(f"Hybrid search returned {len(final_results)} results")
            
            return final_results
            
        except Exception as e:
            app_logger.error(f"Error in hybrid search: {e}")
            raise
    
    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        alpha: float = 0.5,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Merge results using Reciprocal Rank Fusion.
        
        RRF Formula: score = Σ(1 / (k + rank))
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            alpha: Weight for vector results (0-1)
            k: RRF constant (typically 60)
        
        Returns:
            Merged and ranked results
        """
        # Build score dictionary
        scores = defaultdict(float)
        doc_data = {}
        
        # Process vector results
        for rank, result in enumerate(vector_results, start=1):
            doc_id = result['chunk_id']
            rrf_score = 1.0 / (k + rank)
            scores[doc_id] += alpha * rrf_score
            doc_data[doc_id] = result
        
        # Process keyword results
        for rank, result in enumerate(keyword_results, start=1):
            doc_id = result['chunk_id']
            rrf_score = 1.0 / (k + rank)
            scores[doc_id] += (1 - alpha) * rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result
        
        # Sort by RRF score
        ranked_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build final results
        merged_results = []
        for doc_id, score in ranked_docs:
            result = doc_data[doc_id].copy()
            result['hybrid_score'] = score
            merged_results.append(result)
        
        return merged_results
    
    def explain_search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Get detailed explanation of search results.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            Dictionary with search explanation
        """
        try:
            # Get results from both methods
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            vector_results = self.os_client.vector_search(
                query_vector=query_embedding.tolist(),
                top_k=top_k
            )
            
            keyword_results = self.os_client.keyword_search(
                query_text=query,
                top_k=top_k
            )
            
            hybrid_results = self.search(query, top_k=top_k)
            
            return {
                "query": query,
                "vector_results": [
                    {"chunk_id": r['chunk_id'], "score": r['score'], "title": r['paper_title']}
                    for r in vector_results
                ],
                "keyword_results": [
                    {"chunk_id": r['chunk_id'], "score": r['score'], "title": r['paper_title']}
                    for r in keyword_results
                ],
                "hybrid_results": [
                    {"chunk_id": r['chunk_id'], "score": r['hybrid_score'], "title": r['paper_title']}
                    for r in hybrid_results
                ],
                "alpha": self.alpha
            }
            
        except Exception as e:
            app_logger.error(f"Error explaining search: {e}")
            raise


# Global hybrid search instance
_hybrid_search: Optional[HybridSearch] = None


def get_hybrid_search() -> HybridSearch:
    """Get or create global hybrid search instance."""
    global _hybrid_search
    if _hybrid_search is None:
        _hybrid_search = HybridSearch()
    return _hybrid_search