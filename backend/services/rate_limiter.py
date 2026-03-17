import os
import json
import logging
from datetime import datetime
from typing import Optional
import redis
from fastapi import Request, HTTPException, status
from database.redis_client import redis_client

logger = logging.getLogger("app_logger")

class RateLimiter:
    """
    A unified Redis-backed Rate Limiter for FastAPI.
    Tracks requests based on an identifier (like an IP address or authenticated email) 
    against a specific endpoint alias.
    """
    
    def __init__(self, endpoint_name: str, max_requests: int = 10, window_seconds: int = 60):
        """
        :param endpoint_name: A unique string alias for the endpoint being protected (e.g. 'upload_resume').
        :param max_requests: Maximum allowed requests within the time window.
        :param window_seconds: The sliding window timeframe in seconds.
        """
        self.endpoint_name = endpoint_name
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request, identifier: Optional[str] = None):
        """
        Intercepts the route call as a FastAPI dependency.
        """
        # 1. Determine Identity (Fallback to Client IP if no identifier passed/available)
        client_ip = request.client.host if request.client else "unknown"
        user_ident = identifier or client_ip

        # 2. Construct Redis Key
        redis_key = f"ratelimit:{user_ident}:{self.endpoint_name}"

        try:
            # 3. Increment Counter
            current_count = redis_client.incr(redis_key)
            
            # 4. If it's the first request in the window, set the TTL expiration
            if current_count == 1:
                redis_client.expire(redis_key, self.window_seconds)
                
            # 5. Check if Limit Exceeded
            if current_count > self.max_requests:
                ttl = redis_client.ttl(redis_key)
                retry_after = ttl if ttl > 0 else self.window_seconds
                
                logger.warning(
                    f"Rate limit exceeded | User: {user_ident} | "
                    f"Endpoint: {self.endpoint_name} | Limit: {self.max_requests}/{self.window_seconds}s"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
                
        except redis.RedisError as e:
            # Fail open if Redis drops connection so we don't block legitimate traffic
            logger.error(f"Redis connection failed during rate limiting: {str(e)}")
            pass 
        
        return True
