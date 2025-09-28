import time
import asyncio
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException, Request, status
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation"""
    
    def __init__(self):
        self._windows: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit"""
        
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds
            
            # Clean old entries
            window = self._windows[key]
            while window and window[0] < window_start:
                window.popleft()
            
            current_count = len(window)
            
            if current_count >= limit:
                retry_after = int(window[0] - window_start) if window else window_seconds
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": int(now + retry_after),
                    "retry_after": retry_after
                }
            
            # Add current request
            window.append(now)
            
            return True, {
                "limit": limit,
                "remaining": limit - (current_count + 1),
                "reset": int(now + window_seconds),
                "retry_after": 0
            }


class RateLimitManager:
    def __init__(self):
        self.limiter = SlidingWindowRateLimiter()
        
        # Rate limit configurations
        self.limits = {
            "checkpoint_creation": (100, 60),  # 100 requests per minute
            "tracking_query": (200, 60),       # 200 requests per minute
            "unit_listing": (50, 60),          # 50 requests per minute
            "global": (1000, 60)               # 1000 requests per minute globally
        }
    
    async def check_rate_limit(
        self,
        request: Request,
        operation: str,
        identifier: Optional[str] = None
    ) -> None:
        """Check rate limit for operation"""
        
        # Generate rate limit key
        client_ip = self._get_client_ip(request)
        user_id = identifier or "anonymous"
        rate_key = f"{operation}:{user_id}:{client_ip}"
        global_key = f"global:{client_ip}"
        
        # Check operation-specific limit
        if operation in self.limits:
            limit, window = self.limits[operation]
            allowed, info = await self.limiter.is_allowed(rate_key, limit, window)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {rate_key}: {info}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {operation}",
                    headers={
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset"]),
                        "Retry-After": str(info["retry_after"])
                    }
                )
        
        # Check global limit
        global_limit, global_window = self.limits["global"]
        allowed, info = await self.limiter.is_allowed(global_key, global_limit, global_window)
        
        if not allowed:
            logger.warning(f"Global rate limit exceeded for {client_ip}: {info}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Global rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"])
                }
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
