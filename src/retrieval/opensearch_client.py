"""
OpenSearch client for vector storage and retrieval.
Handles embedding indexing and vector similarity search.
"""
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, helpers
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import settings
from src.core.logging_config import app_logger


class OpenSearchClient:
    """
    OpenSearch client for vector search operations.
    
    Features:
    - Index creation and management
    - Bulk indexing with batching
    - KNN vector search
    - Connection retry logic
    """
    
    def __init__(self):
        """Initialize OpenSearch client."""
        try:
            self.client = OpenSearch(
                hosts=[{
                    'host': settings.opensearch_host,
                    'port': settings.opensearch_port
                }],
                http_auth=(settings.opensearch_user, settings.opensearch_password) if settings.opensearch_user else None,
                use_ssl=settings.opensearch_use_ssl,
                verify_certs=settings.opensearch_verify_certs,
                ssl_show_warn=False,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            self.index_name = settings.opensearch_index_name
            
            # Test connection
            if self.client.ping():
                app_logger.info("✅ OpenSearch connection successful")
            else:
                raise ConnectionError("Failed to ping OpenSearch")
                
        except Exception as e:
            app_logger.error(f"❌ Failed to connect to OpenSearch: {e}")
            raise
    
    def create_index(self, index_name: Optional[str] = None, force_recreate: bool = False):
        """
        Create OpenSearch index with vector field.
        
        Args:
            index_name: Name of the index
            force_recreate: If True, delete existing index first
        """
        index_name = index_name or self.index_name
        
        try:
            # Check if index exists
            if self.client.indices.exists(index=index_name):
                if force_recreate:
                    app_logger.warning(f"Deleting existing index: {index_name}")
                    self.client.indices.delete(index=index_name)
                else:
                    app_logger.info(f"Index '{index_name}' already exists")
                    return
            
            # Index configuration
            index_body = {
                "settings": {
                    "index": {
                        "number_of_shards": 2,
                        "number_of_replicas": 1,
                        "knn": True,  # Enable KNN
                        "knn.algo_param.ef_search": 100  # KNN search parameter
                    }
                },
                "mappings": {
                    "properties": {
                        "chunk_id": {"type": "integer"},
                        "paper_id": {"type": "integer"},
                        "arxiv_id": {"type": "keyword"},
                        "chunk_index": {"type": "integer"},
                        "content": {"type": "text"},
                        "chunk_type": {"type": "keyword"},
                        
                        # Paper metadata
                        "paper_title": {"type": "text"},
                        "paper_authors": {"type": "text"},
                        "paper_abstract": {"type": "text"},
                        "paper_categories": {"type": "keyword"},
                        "published_date": {"type": "date"},
                        
                        # Vector embedding field
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": settings.embedding_dimension,
                            "method": {
                                "name": "hnsw",  # Hierarchical Navigable Small World
                                "space_type": "cosinesimil",  # Cosine similarity
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 16
                                }
                            }
                        },
                        
                        # Timestamps
                        "indexed_at": {"type": "date"}
                    }
                }
            }
            
            self.client.indices.create(index=index_name, body=index_body)
            app_logger.info(f"✅ Created index: {index_name}")
            
        except Exception as e:
            app_logger.error(f"Error creating index: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def index_document(
        self,
        document: Dict[str, Any],
        index_name: Optional[str] = None
    ) -> bool:
        """
        Index a single document.
        
        Args:
            document: Document to index
            index_name: Name of the index
        
        Returns:
            True if successful
        """
        index_name = index_name or self.index_name
        
        try:
            doc_id = f"{document['paper_id']}_{document['chunk_index']}"
            
            response = self.client.index(
                index=index_name,
                id=doc_id,
                body=document,
                refresh=True
            )
            
            if response['result'] in ['created', 'updated']:
                return True
            else:
                app_logger.warning(f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            app_logger.error(f"Error indexing document: {e}")
            raise
    
    def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]],
        index_name: Optional[str] = None,
        chunk_size: int = 500
    ) -> Dict[str, int]:
        """
        Bulk index multiple documents.
        
        Args:
            documents: List of documents to index
            index_name: Name of the index
            chunk_size: Number of documents per bulk request
        
        Returns:
            Dictionary with success/failure counts
        """
        index_name = index_name or self.index_name
        
        try:
            app_logger.info(f"Bulk indexing {len(documents)} documents")
            
            # Prepare bulk actions
            actions = []
            for doc in documents:
                action = {
                    "_index": index_name,
                    "_id": f"{doc['paper_id']}_{doc['chunk_index']}",
                    "_source": doc
                }
                actions.append(action)
            
            # Execute bulk indexing
            success, failed = helpers.bulk(
                self.client,
                actions,
                chunk_size=chunk_size,
                raise_on_error=False,
                stats_only=True
            )
            
            app_logger.info(f"✅ Bulk indexing complete - Success: {success}, Failed: {failed}")
            
            return {"success": success, "failed": failed}
            
        except Exception as e:
            app_logger.error(f"Error in bulk indexing: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def vector_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_query: Optional[Dict] = None,
        index_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_query: Optional filter query
            index_name: Name of the index
        
        Returns:
            List of search results with scores
        """
        index_name = index_name or self.index_name
        
        try:
            query = {
                "size": top_k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": top_k
                        }
                    }
                }
            }
            
            # Add filter if provided
            if filter_query:
                query["query"] = {
                    "bool": {
                        "must": [query["query"]],
                        "filter": filter_query
                    }
                }
            
            response = self.client.search(index=index_name, body=query)
            
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'score': hit['_score'],
                    'chunk_id': hit['_source']['chunk_id'],
                    'paper_id': hit['_source']['paper_id'],
                    'arxiv_id': hit['_source']['arxiv_id'],
                    'content': hit['_source']['content'],
                    'paper_title': hit['_source']['paper_title'],
                    'paper_authors': hit['_source']['paper_authors'],
                    'chunk_type': hit['_source']['chunk_type']
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            app_logger.error(f"Error in vector search: {e}")
            raise
    
    def keyword_search(
        self,
        query_text: str,
        top_k: int = 10,
        fields: Optional[List[str]] = None,
        index_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search using BM25.
        
        Args:
            query_text: Search query text
            top_k: Number of results
            fields: Fields to search in
            index_name: Name of the index
        
        Returns:
            List of search results
        """
        index_name = index_name or self.index_name
        fields = fields or ["content^2", "paper_title^1.5", "paper_abstract"]
        
        try:
            query = {
                "size": top_k,
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": fields,
                        "type": "best_fields"
                    }
                }
            }
            
            response = self.client.search(index=index_name, body=query)
            
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'score': hit['_score'],
                    'chunk_id': hit['_source']['chunk_id'],
                    'paper_id': hit['_source']['paper_id'],
                    'arxiv_id': hit['_source']['arxiv_id'],
                    'content': hit['_source']['content'],
                    'paper_title': hit['_source']['paper_title'],
                    'paper_authors': hit['_source']['paper_authors'],
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            app_logger.error(f"Error in keyword search: {e}")
            raise
    
    def delete_by_paper_id(self, paper_id: int, index_name: Optional[str] = None):
        """Delete all chunks for a paper."""
        index_name = index_name or self.index_name
        
        try:
            query = {
                "query": {
                    "term": {"paper_id": paper_id}
                }
            }
            
            response = self.client.delete_by_query(index=index_name, body=query)
            deleted_count = response.get('deleted', 0)
            
            app_logger.info(f"Deleted {deleted_count} chunks for paper_id: {paper_id}")
            
        except Exception as e:
            app_logger.error(f"Error deleting chunks: {e}")
            raise
    
    def get_index_stats(self, index_name: Optional[str] = None) -> Dict[str, Any]:
        """Get index statistics."""
        index_name = index_name or self.index_name
        
        try:
            stats = self.client.indices.stats(index=index_name)
            doc_count = stats['indices'][index_name]['total']['docs']['count']
            size_bytes = stats['indices'][index_name]['total']['store']['size_in_bytes']
            
            return {
                "document_count": doc_count,
                "size_mb": round(size_bytes / (1024 * 1024), 2)
            }
        except Exception as e:
            app_logger.error(f"Error getting index stats: {e}")
            return {}


# Global OpenSearch client instance
_opensearch_client: Optional[OpenSearchClient] = None


def get_opensearch_client() -> OpenSearchClient:
    """Get or create global OpenSearch client."""
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = OpenSearchClient()
    return _opensearch_client