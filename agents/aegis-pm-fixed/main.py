"""Application entrypoint for Aegis PM."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from api.middleware import install_middleware
from api.routes import router
from config import get_settings


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(title="Aegis PM", version="1.0.0")
    install_middleware(app)
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=False)
