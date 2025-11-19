"""
Embeddings generator using Sentence Transformers.
Generates vector embeddings for semantic search.
"""
from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from src.core.config import settings
from src.core.logging_config import app_logger


class EmbeddingsGenerator:
    """Generate embeddings for text using Sentence Transformers."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embeddings generator.
        
        Args:
            model_name: Name of sentence transformer model
                       Default: 'all-MiniLM-L6-v2' (fast, 384 dims)
        """
        self.model_name = model_name or getattr(settings, 'embedding_model', 'all-MiniLM-L6-v2')
        self._model = None
        app_logger.info(f"Initializing embeddings generator with model: {self.model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model."""
        if self._model is None:
            app_logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            app_logger.info(f"✅ Model loaded: {self.model_name}")
        return self._model
    
    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        if not text or not text.strip():
            app_logger.warning("Empty text provided for embedding")
            return np.zeros(self.embedding_dim)
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            return embedding
        except Exception as e:
            app_logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.embedding_dim)
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings
        """
        if not texts:
            return np.array([])
        
        try:
            app_logger.info(f"Generating embeddings for {len(texts)} texts...")
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            app_logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            app_logger.error(f"Error generating batch embeddings: {e}")
            return np.zeros((len(texts), self.embedding_dim))
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding optimized for query.
        
        Args:
            query: Search query
            
        Returns:
            Query embedding vector
        """
        return self.generate_embedding(query)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0-1)
        """
        from numpy.linalg import norm
        
        if embedding1.size == 0 or embedding2.size == 0:
            return 0.0
        
        cos_sim = np.dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))
        return float(cos_sim)
    
    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: Array of candidate embeddings
            top_k: Number of top results
            
        Returns:
            List of (index, similarity_score) tuples
        """
        if candidate_embeddings.size == 0:
            return []
        
        from numpy.linalg import norm
        
        similarities = np.dot(candidate_embeddings, query_embedding) / (
            norm(candidate_embeddings, axis=1) * norm(query_embedding)
        )
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [(int(idx), float(similarities[idx])) for idx in top_indices]
        return results


# Global instance
_embedding_generator = None


def get_embedding_generator() -> EmbeddingsGenerator:
    """Get global embeddings generator instance."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingsGenerator()
    return _embedding_generator