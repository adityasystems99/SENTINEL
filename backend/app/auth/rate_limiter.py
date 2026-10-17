"""In-memory thread-safe sliding window rate limiter without Redis.
Provides route-level and IP-based rate limiting suitable for single-instance deployments.
"""
import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request, status
from ..config import settings


class InMemoryRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._hits: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(
        self, client_key: str, max_requests: int, window_seconds: float = 60.0
    ) -> Tuple[bool, int]:
        """Check if client_key has exceeded max_requests in the rolling window."""
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Filter timestamps in sliding window
            timestamps = [ts for ts in self._hits[client_key] if ts > window_start]
            if len(timestamps) >= max_requests:
                earliest = timestamps[0]
                retry_after = int(window_seconds - (now - earliest)) + 1
                self._hits[client_key] = timestamps
                return True, max(1, retry_after)

            timestamps.append(now)
            self._hits[client_key] = timestamps
            return False, 0

    def reset(self):
        """Reset all tracked rate limit buckets (useful for tests)."""
        with self._lock:
            self._hits.clear()


rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """Safely obtain client IP address without blindly trusting spoofed headers."""
    if settings.behind_trusted_proxy:
        real_ip = request.headers.get("x-real-ip") or request.headers.get("cf-connecting-ip")
        if real_ip:
            return real_ip.strip()

        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # When behind a trusted proxy, taking the rightmost non-internal entry avoids client spoofing
            hops = [h.strip() for h in forwarded.split(",") if h.strip()]
            if hops:
                return hops[-1]

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


def check_rate_limit(
    max_requests: int = 120,
    window_seconds: float = 60.0,
    route_scope: str = "general",
):
    """Factory for FastAPI dependency to enforce rate limits per IP and route scope."""
    async def dependency(request: Request):
        client_ip = get_client_ip(request)
        key = f"{route_scope}:{client_ip}"
        is_limited, retry_after = rate_limiter.is_rate_limited(
            key, max_requests=max_requests, window_seconds=window_seconds
        )
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {route_scope}. Maximum {max_requests} requests per {int(window_seconds)}s.",
                headers={"Retry-After": str(retry_after)},
            )
    return dependency
