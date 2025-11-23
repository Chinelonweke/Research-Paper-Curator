"""Redis caching service for API responses."""
import os
import redis
import json
from typing import Any, Optional
from src.core.logging_config import app_logger as logger


class RedisCache:
    """Redis cache manager."""

    def __init__(self):
        # Use REDIS_URL from Heroku
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        try:
            # Handle both redis:// and rediss:// (SSL)
            if redis_url.startswith("rediss://"):
                # SSL connection - disable certificate verification for Heroku Redis
                self.client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    ssl_cert_reqs=None  # Disable SSL certificate verification
                )
            else:
                # Non-SSL connection
                self.client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
            
            self.client.ping()
            log_url = redis_url.split('@')[-1] if '@' in redis_url else redis_url
            logger.info(f"✅ Redis connected: {log_url}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.client:
            return None
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.client:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.client:
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")
            return 0


# Singleton instance
_redis_cache = None

def get_redis_cache() -> RedisCache:
    """Get Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache

# Export for backward compatibility
cache = get_redis_cache()
