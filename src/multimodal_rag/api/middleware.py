"""FastAPI middleware: error handlers, request logging, metrics."""

from __future__ import annotations

import time
from collections.abc import Callable

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from multimodal_rag.exceptions import (
    AuthenticationError,
    DatasetError,
    EmbeddingProviderError,
    GeneratorProviderError,
    MultimodalRagError,
    PipelineError,
    ProviderError,
    ProviderNotAvailableError,
    RateLimitExceededError,
    RerankerProviderError,
    RetrievalError,
    ValidationError,
    VectorStoreConnectionError,
    VectorStoreError,
)
from multimodal_rag.monitoring import ERRORS, REQUESTS, REQUEST_LATENCY

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Error → HTTP status code mapping
# ---------------------------------------------------------------------------


_STATUS_MAP: dict[type[Exception], int] = {
    ValidationError: 400,
    AuthenticationError: 401,
    RateLimitExceededError: 429,
    ProviderNotAvailableError: 503,
    VectorStoreConnectionError: 503,
    DatasetError: 422,
    EmbeddingProviderError: 502,
    RerankerProviderError: 502,
    GeneratorProviderError: 502,
    ProviderError: 502,
    RetrievalError: 500,
    PipelineError: 500,
    VectorStoreError: 500,
    MultimodalRagError: 500,
}


def _status_for(exc: Exception) -> int:
    for cls, code in _STATUS_MAP.items():
        if isinstance(exc, cls):
            return code
    return 500


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record request count + latency for every HTTP call."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            dt = time.perf_counter() - start
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code if response else 500
            REQUESTS.labels(
                method=method, endpoint=endpoint, status=str(status_code)
            ).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(dt)


class StructlogMiddleware(BaseHTTPMiddleware):
    """Emit one structured log line per request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
            dt = time.perf_counter() - start
            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(dt * 1000, 2),
                client=request.client.host if request.client else "-",
            )
            return response
        except Exception:
            dt = time.perf_counter() - start
            log.exception(
                "http_request_error",
                method=request.method,
                path=request.url.path,
                duration_ms=round(dt * 1000, 2),
            )
            raise


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MultimodalRagError)
    async def _handle_app_error(_: Request, exc: MultimodalRagError) -> JSONResponse:
        code = _status_for(exc)
        ERRORS.labels(category=exc.__class__.__name__).inc()
        log.warning("app_error", error=exc.__class__.__name__, detail=str(exc))
        return JSONResponse(
            status_code=code,
            content={
                "error": {
                    "error": exc.__class__.__name__,
                    "detail": str(exc),
                    "code": str(code),
                }
            },
        )

    @app.exception_handler(Exception)
    async def _handle_unknown(_: Request, exc: Exception) -> JSONResponse:
        ERRORS.labels(category="Unknown").inc()
        log.exception("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "error": "InternalServerError",
                    "detail": "an unexpected error occurred",
                    "code": "500",
                }
            },
        )
