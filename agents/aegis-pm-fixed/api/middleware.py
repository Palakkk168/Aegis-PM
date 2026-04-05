"""FastAPI middleware and exception handling."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from observability.logger import configure_logging
from observability.metrics import metrics_registry


logger = configure_logging()


def install_middleware(app: FastAPI) -> None:
    """Install request correlation and exception handling middleware."""

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", uuid4().hex)
        request.state.correlation_id = correlation_id
        await metrics_registry.increment("request_count")
        logger.info("http.request", path=request.url.path, method=request.method, correlation_id=correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "http.error",
            path=request.url.path,
            method=request.method,
            correlation_id=getattr(request.state, "correlation_id", None),
            error=str(exc),
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
