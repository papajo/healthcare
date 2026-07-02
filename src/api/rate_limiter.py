"""Rate limiting middleware — token bucket algorithm.

Provides per-client rate limiting for sensitive endpoints.
In production, replace with Redis-backed implementation.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiter middleware.

    Args:
        app: FastAPI application
        default_limit: Max requests per window (default: 100)
        default_window: Window duration in seconds (default: 60)
        path_limits: Per-path rate limits as {path_prefix: (limit, window)}
    """

    def __init__(
        self,
        app,
        default_limit: int = 100,
        default_window: int = 60,
        path_limits: dict[str, tuple[int, int]] | None = None,
    ) -> None:
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.path_limits = path_limits or {
            "/v1/urgency/classify": (10, 60),  # 10 per minute
            "/v1/claims": (30, 60),  # 30 per minute
            "/v1/consent": (20, 60),  # 20 per minute
            "/v1/auth/login": (5, 60),  # 5 per minute
        }
        # Token buckets: client_key -> (tokens, last_refill)
        self._buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(self.default_limit), time.time())
        )

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Use X-Forwarded-For if behind proxy, else client host
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _get_limits(self, path: str) -> tuple[int, int]:
        """Get rate limit for a path. Falls back to default."""
        for prefix, limits in self.path_limits.items():
            if path.startswith(prefix):
                return limits
        return self.default_limit, self.default_window

    def _consume_token(self, client_key: str, limit: int, window: int) -> bool:
        """Try to consume a rate limit token. Returns True if allowed."""
        now = time.time()
        tokens, last_refill = self._buckets[client_key]

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        refill_rate = limit / window  # tokens per second
        tokens = min(limit, tokens + elapsed * refill_rate)

        if tokens < 1:
            return False

        self._buckets[client_key] = (tokens - 1, now)
        return True

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Skip rate limiting for health checks, docs, and test mode
        if request.url.path in ("/health", "/ready", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Skip in test mode (testserver host or TESTING env var)
        if request.url.hostname in ("testclient", "testserver") or os.environ.get("TESTING"):
            return await call_next(request)

        client_key = self._get_client_key(request)
        limit, window = self._get_limits(request.url.path)

        if not self._consume_token(client_key, limit, window):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": window,
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        tokens, _ = self._buckets[client_key]
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, int(tokens)))

        return response
