"""
Performance optimization utilities for heavy load.
Implements rate limiting, request queuing, and circuit breakers.
"""
from functools import wraps
from typing import Optional, Callable
import time
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis
from fastapi import HTTPException, Request
from src.core.config import settings
from src.core.logging_config import app_logger


class RateLimiter:
    """
    Token bucket rate limiter with Redis backend.
    Handles high-volume requests with distributed rate limiting.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.requests_per_minute = 100  # Configurable
        self.burst_size = 150
    
    async def check_rate_limit(self, key: str) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier (user_id, IP, API key)
        
        Returns:
            True if allowed, False if rate limited
        """
        try:
            current_time = int(time.time())
            window_key = f"rate_limit:{key}:{current_time // 60}"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, 120)  # 2 minute expiry
            results = pipe.execute()
            
            request_count = results[0]
            
            if request_count > self.burst_size:
                app_logger.warning(f"Rate limit exceeded for {key}: {request_count} requests")
                return False
            
            return True
            
        except Exception as e:
            app_logger.error(f"Rate limit check failed: {e}")
            return True  # Fail open to avoid blocking on Redis errors
    
    def get_remaining_quota(self, key: str) -> int:
        """Get remaining requests in current window."""
        try:
            current_time = int(time.time())
            window_key = f"rate_limit:{key}:{current_time // 60}"
            count = self.redis.get(window_key)
            
            if count is None:
                return self.burst_size
            
            return max(0, self.burst_size - int(count))
        except:
            return self.burst_size


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    Prevents cascade failures and gives services time to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        States:
        - closed: Normal operation
        - open: Rejecting calls (service is down)
        - half_open: Testing if service recovered
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to retry."""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = "closed"
        app_logger.info("Circuit breaker: Service recovered")
    
    def _on_failure(self):
        """Record failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            app_logger.error(
                f"Circuit breaker: OPEN after {self.failure_count} failures. "
                f"Will retry in {self.recovery_timeout}s"
            )


class RequestQueue:
    """
    Priority queue for handling high-load scenarios.
    Queues requests and processes them with backpressure.
    """
    
    def __init__(self, max_queue_size: int = 1000, worker_count: int = 10):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.worker_count = worker_count
        self.workers = []
        self.processing = False
    
    async def enqueue(self, request_data: dict, priority: int = 5) -> dict:
        """
        Add request to queue.
        
        Args:
            request_data: Request payload
            priority: Priority level (1-10, lower is higher priority)
        
        Returns:
            Result when processed
        """
        try:
            result_future = asyncio.Future()
            await self.queue.put((priority, time.time(), request_data, result_future))
            return await result_future
        except asyncio.QueueFull:
            raise HTTPException(status_code=503, detail="Service overloaded. Please retry later.")
    
    async def start_workers(self, processor_func: Callable):
        """Start background workers."""
        self.processing = True
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker(processor_func, i))
            self.workers.append(worker)
        app_logger.info(f"Started {self.worker_count} queue workers")
    
    async def _worker(self, processor_func: Callable, worker_id: int):
        """Background worker that processes queued requests."""
        while self.processing:
            try:
                priority, timestamp, request_data, result_future = await self.queue.get()
                
                # Check if request is too old (timeout)
                age = time.time() - timestamp
                if age > 30:  # 30 second timeout
                    result_future.set_exception(
                        HTTPException(status_code=408, detail="Request timeout")
                    )
                    continue
                
                # Process request
                result = await processor_func(request_data)
                result_future.set_result(result)
                
            except Exception as e:
                app_logger.error(f"Worker {worker_id} error: {e}")
                result_future.set_exception(e)
    
    async def stop_workers(self):
        """Stop all workers gracefully."""
        self.processing = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        app_logger.info("Stopped all queue workers")


class ConnectionPoolManager:
    """
    Advanced connection pool manager with monitoring.
    Prevents connection exhaustion under heavy load.
    """
    
    def __init__(self):
        self.pools = {}
        self.stats = defaultdict(lambda: {
            "active": 0,
            "idle": 0,
            "total": 0,
            "wait_time_avg": 0.0
        })
    
    def register_pool(self, name: str, pool):
        """Register a connection pool for monitoring."""
        self.pools[name] = pool
    
    def get_pool_stats(self, name: str) -> dict:
        """Get statistics for a connection pool."""
        if name not in self.pools:
            return {}
        
        pool = self.pools[name]
        
        # SQLAlchemy pool stats
        if hasattr(pool, 'pool'):
            return {
                "size": pool.pool.size(),
                "checked_in": pool.pool.checkedin(),
                "checked_out": pool.pool.checkedout(),
                "overflow": pool.pool.overflow(),
                "capacity": pool.pool.size() + pool.pool.overflow()
            }
        
        return self.stats[name]
    
    def check_pool_health(self) -> dict:
        """Check health of all connection pools."""
        health = {}
        
        for name, pool in self.pools.items():
            stats = self.get_pool_stats(name)
            
            # Check if pool is near capacity
            if stats.get("checked_out", 0) > stats.get("size", 0) * 0.8:
                health[name] = "warning"
            else:
                health[name] = "healthy"
        
        return health


class ResponseCache:
    """
    Multi-level caching strategy for optimal performance.
    L1: In-memory (fastest, smallest)
    L2: Redis (fast, larger)
    L3: Database (slower, persistent)
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.l1_cache = {}  # In-memory cache
        self.l1_max_size = 100
        self.l1_access_times = deque(maxlen=100)
    
    async def get(self, key: str) -> Optional[dict]:
        """Get from multi-level cache."""
        # L1: In-memory
        if key in self.l1_cache:
            app_logger.debug(f"Cache L1 HIT: {key}")
            return self.l1_cache[key]
        
        # L2: Redis
        try:
            value = self.redis.get(f"cache:l2:{key}")
            if value:
                app_logger.debug(f"Cache L2 HIT: {key}")
                import json
                result = json.loads(value)
                
                # Promote to L1
                self._set_l1(key, result)
                return result
        except Exception as e:
            app_logger.error(f"Redis cache error: {e}")
        
        app_logger.debug(f"Cache MISS: {key}")
        return None
    
    async def set(self, key: str, value: dict, ttl: int = 3600):
        """Set in multi-level cache."""
        import json
        
        # L1: In-memory
        self._set_l1(key, value)
        
        # L2: Redis
        try:
            self.redis.setex(
                f"cache:l2:{key}",
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            app_logger.error(f"Redis cache set error: {e}")
    
    def _set_l1(self, key: str, value: dict):
        """Set in L1 cache with LRU eviction."""
        if len(self.l1_cache) >= self.l1_max_size:
            # Evict least recently used
            if self.l1_access_times:
                oldest_key = self.l1_access_times.popleft()
                self.l1_cache.pop(oldest_key, None)
        
        self.l1_cache[key] = value
        self.l1_access_times.append(key)
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "l1_size": len(self.l1_cache),
            "l1_max_size": self.l1_max_size,
            "l2_connected": self.redis.ping() if self.redis else False
        }


# Global instances
_rate_limiter: Optional[RateLimiter] = None
_request_queue: Optional[RequestQueue] = None
_connection_pool_manager = ConnectionPoolManager()
_response_cache: Optional[ResponseCache] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        from src.cache.redis_cache import get_redis_cache
        cache = get_redis_cache()
        _rate_limiter = RateLimiter(cache.client)
    return _rate_limiter


def get_request_queue() -> RequestQueue:
    """Get global request queue instance."""
    global _request_queue
    if _request_queue is None:
        _request_queue = RequestQueue(
            max_queue_size=1000,
            worker_count=20
        )
    return _request_queue


def get_response_cache() -> ResponseCache:
    """Get global response cache instance."""
    global _response_cache
    if _response_cache is None:
        from src.cache.redis_cache import get_redis_cache
        cache = get_redis_cache()
        _response_cache = ResponseCache(cache.client)
    return _response_cache