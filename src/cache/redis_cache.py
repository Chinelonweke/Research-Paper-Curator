"""
Redis caching layer for queries and embeddings.
"""
import json
import pickle
from typing import Any, Optional, List
import redis
from src.core.config import settings
from src.core.logging_config import app_logger


class RedisCache:
    """Redis cache for query results and embeddings."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        default_ttl: int = 3600
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.host = host or getattr(settings, 'redis_host', 'localhost')
        self.port = port or getattr(settings, 'redis_port', 6379)
        self.db = db
        self.password = password or getattr(settings, 'redis_password', None)
        self.default_ttl = default_ttl
        
        self._client = None
        self._connected = False
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client (lazy initialization)."""
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=False,  # We'll handle encoding
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self._client.ping()
                self._connected = True
                app_logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
            except redis.ConnectionError as e:
                app_logger.warning(f"⚠️ Could not connect to Redis: {e}")
                app_logger.warning("Cache will be disabled")
                self._connected = False
        return self._client
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self._connected:
            return False
        try:
            self.client.ping()
            return True
        except:
            self._connected = False
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.is_connected():
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try to unpickle
            try:
                return pickle.loads(value)
            except:
                # If unpickle fails, return as string
                return value.decode('utf-8')
                
        except Exception as e:
            app_logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = default)
            
        Returns:
            Success boolean
        """
        if not self.is_connected():
            return False
        
        try:
            # Pickle the value
            pickled = pickle.dumps(value)
            
            # Set with TTL
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, pickled)
            
            return True
        except Exception as e:
            app_logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Success boolean
        """
        if not self.is_connected():
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            app_logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache entries."""
        if not self.is_connected():
            return False
        
        try:
            self.client.flushdb()
            app_logger.info("✅ Cache cleared")
            return True
        except Exception as e:
            app_logger.error(f"Cache clear error: {e}")
            return False
    
    def get_query_cache_key(self, question: str, top_k: int) -> str:
        """Generate cache key for a query."""
        import hashlib
        query_hash = hashlib.md5(f"{question}:{top_k}".encode()).hexdigest()
        return f"query:{query_hash}"
    
    def get_embedding_cache_key(self, text: str) -> str:
        """Generate cache key for an embedding."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{text_hash}"
    
    def cache_query_result(self, question: str, top_k: int, result: dict, ttl: int = 3600) -> bool:
        """
        Cache a query result.
        
        Args:
            question: Question text
            top_k: Number of results
            result: Result dictionary
            ttl: Time to live
            
        Returns:
            Success boolean
        """
        key = self.get_query_cache_key(question, top_k)
        return self.set(key, result, ttl)
    
    def get_cached_query_result(self, question: str, top_k: int) -> Optional[dict]:
        """
        Get cached query result.
        
        Args:
            question: Question text
            top_k: Number of results
            
        Returns:
            Cached result or None
        """
        key = self.get_query_cache_key(question, top_k)
        result = self.get(key)
        if result:
            app_logger.info(f"✅ Cache HIT for query: {question[:50]}")
        return result
    
    def cache_embedding(self, text: str, embedding: Any, ttl: int = 86400) -> bool:
        """
        Cache an embedding (24 hour default TTL).
        
        Args:
            text: Text that was embedded
            embedding: Embedding vector
            ttl: Time to live
            
        Returns:
            Success boolean
        """
        key = self.get_embedding_cache_key(text)
        return self.set(key, embedding, ttl)
    
    def get_cached_embedding(self, text: str) -> Optional[Any]:
        """
        Get cached embedding.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            Cached embedding or None
        """
        key = self.get_embedding_cache_key(text)
        return self.get(key)


# Global cache instance
_redis_cache = None


def get_redis_cache() -> RedisCache:
    """Get global Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache