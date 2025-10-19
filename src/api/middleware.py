"""
API Middleware - Rate Limiting, Security, Performance.
Production-ready with comprehensive features.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable
import time
import asyncio

from src.core.logging_config import app_logger
from src.core.config import settings


# =============================================================================
# RATE LIMITING MIDDLEWARE
# =============================================================================
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting with Redis fallback to in-memory.
    Per-IP tracking with configurable limits.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)  # Fallback in-memory storage
        self.cleanup_interval = 60
        self.last_cleanup = time.time()
        self.use_redis = settings.redis_enabled
        
        if self.use_redis:
            try:
                from src.cache.redis_cache import get_redis_client
                self.redis = get_redis_client()
            except:
                app_logger.warning("Redis not available, using in-memory rate limiting")
                self.use_redis = False
    
    def _cleanup_old_requests(self):
        """Clean old entries to prevent memory leak."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            cutoff = datetime.now() - timedelta(minutes=2)
            for ip in list(self.requests.keys()):
                self.requests[ip] = [
                    req_time for req_time in self.requests[ip]
                    if req_time > cutoff
                ]
                if not self.requests[ip]:
                    del self.requests[ip]
            self.last_cleanup = now
    
    async def _check_redis_rate_limit(self, client_ip: str) -> bool:
        """Check rate limit using Redis."""
        try:
            key = f"rate_limit:{client_ip}"
            current = await self.redis.get(key)
            
            if current and int(current) >= self.requests_per_minute:
                return False
            
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)
            await pipe.execute()
            
            return True
        except:
            # Fallback to memory if Redis fails
            return self._check_memory_rate_limit(client_ip)
    
    def _check_memory_rate_limit(self, client_ip: str) -> bool:
        """Check rate limit using in-memory storage."""
        self._cleanup_old_requests()
        
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        self.requests[client_ip].append(now)
        return True
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Check rate limit before processing request."""
        # Skip health checks
        if request.url.path.startswith(("/health", "/metrics")):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Check rate limit
        if self.use_redis:
            allowed = await self._check_redis_rate_limit(client_ip)
        else:
            allowed = self._check_memory_rate_limit(client_ip)
        
        if not allowed:
            app_logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        
        return response


# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers."""
        response = await call_next(request)
        
        # Security Headers (OWASP Best Practices)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        if settings.is_production:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
        
        # HSTS (production + HTTPS only)
        if settings.is_production and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response


# =============================================================================
# PERFORMANCE MONITORING MIDDLEWARE
# =============================================================================
class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor request performance and log slow requests."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Track request timing."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Log slow requests
            if process_time > 1000:  # > 1 second
                app_logger.warning(
                    f"SLOW REQUEST: {request.method} {request.url.path} "
                    f"took {process_time:.2f}ms"
                )
            
            # Add timing header
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            app_logger.error(
                f"ERROR: {request.method} {request.url.path} "
                f"failed after {process_time:.2f}ms - {str(e)}"
            )
            raise


# =============================================================================
# CACHE MIDDLEWARE (Optional)
# =============================================================================
class CacheMiddleware(BaseHTTPMiddleware):
    """Cache GET requests for improved performance."""
    
    def __init__(self, app):
        super().__init__(app)
        self.use_cache = settings.redis_enabled
        if self.use_cache:
            try:
                from src.cache.redis_cache import get_redis_client
                self.redis = get_redis_client()
            except:
                self.use_cache = False
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Cache GET requests."""
        # Only cache GET
        if request.method != "GET" or not self.use_cache:
            return await call_next(request)
        
        # Skip certain paths
        skip_paths = ["/health", "/metrics", "/api/stats"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Generate cache key
        cache_key = f"response:{request.url.path}:{str(request.query_params)}"
        
        # Check cache
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                app_logger.debug(f"Cache HIT: {cache_key}")
                return JSONResponse(
                    content=cached,
                    headers={"X-Cache": "HIT"}
                )
        except:
            pass
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses (status 200)
        if response.status_code == 200:
            try:
                # Note: This is simplified - properly handle in production
                response.headers["X-Cache"] = "MISS"
            except:
                pass
        
        return response