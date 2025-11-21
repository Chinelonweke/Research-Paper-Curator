"""Redis caching layer for queries and embeddings."""
import json
import pickle
from typing import Any, Optional, List
import redis
import os
from src.core.logging_config import app_logger


class RedisCache:
    """Redis cache for query results and embeddings."""
    
    def __init__(self, default_ttl: int = 3600):
        """Initialize Redis cache with REDIS_URL from environment."""
        self.default_ttl = default_ttl
        self._client = None
        self._connected = False
        
        # Get Redis URL from environment (Heroku format)
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_url = redis_url
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client (lazy initialization)."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                self._client.ping()
                self._connected = True
                # Hide credentials in log
                log_url = self.redis_url.split('@')[-1] if '@' in self.redis_url else self.redis_url
                app_logger.info(f"✅ Connected to Redis at {log_url}")
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
        """Get value from cache."""
        if not self.is_connected():
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            try:
                return pickle.loads(value)
            except:
                return value.decode('utf-8')
                
        except Exception as e:
            app_logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache."""
        if not self.is_connected():
            return False
        
        try:
            pickled = pickle.dumps(value)
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, pickled)
            return True
        except Exception as e:
            app_logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
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
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.is_connected():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            app_logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def get_query_cache_key(self, question: str, top_k: int) -> str:
        """Generate cache key for a query."""
        import hashlib
        query_hash = hashlib.md5(f"{question}:{top_k}".encode()).hexdigest()
        return f"query:{query_hash}"
    
    def cache_query_result(self, question: str, top_k: int, result: dict, ttl: int = 3600) -> bool:
        """Cache a query result."""
        key = self.get_query_cache_key(question, top_k)
        return self.set(key, result, ttl)
    
    def get_cached_query_result(self, question: str, top_k: int) -> Optional[dict]:
        """Get cached query result."""
        key = self.get_query_cache_key(question, top_k)
        result = self.get(key)
        if result:
            app_logger.info(f"✅ Cache HIT for query: {question[:50]}")
        return result


# Global cache instance
_redis_cache = None

def get_redis_cache() -> RedisCache:
    """Get global Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache
