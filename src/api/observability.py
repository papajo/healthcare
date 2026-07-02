"""Structured logging configuration for HIPAA-compliant observability.

Provides:
- JSON structured logging for machine parsing
- PHI-safe log formatting (redacts sensitive fields)
- Request/response logging middleware
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# ─── PHI Redaction ───────────────────────────────────────────────────────────

# Patterns that look like PHI (SSN, MRN, etc.)
_PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN-REDACTED]"),  # SSN
    (re.compile(r"\bMRN-\d{4,}\b"), "[MRN-REDACTED]"),  # MRN
    (re.compile(r"\b\d{10,}\b"), "[ID-REDACTED]"),  # Long numeric IDs
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL-REDACTED]"),
]


def redact_phi(text: str) -> str:
    """Redact potential PHI from log messages."""
    for pattern, replacement in _PHI_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ─── Structured Logger ───────────────────────────────────────────────────────


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter with PHI redaction."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_phi(record.getMessage()),
        }

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Add exception info
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_structured_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add structured handler
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(handler)


# ─── Request Logging Middleware ──────────────────────────────────────────────


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests with timing and status."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        start = time.time()

        # Log request
        logger = logging.getLogger("http")
        logger.info(
            "Request: %s %s",
            request.method,
            request.url.path,
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params),
                    "client": request.client.host if request.client else "unknown",
                }
            },
        )

        response = await call_next(request)

        # Log response with timing
        duration_ms = (time.time() - start) * 1000
        logger.info(
            "Response: %s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "extra_data": {
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 1),
                    "path": request.url.path,
                }
            },
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        return response
