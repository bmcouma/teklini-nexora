"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nexora.api.db import init_db
from nexora.api.routes import router
from nexora.config.settings import get_settings

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_security()
    app = FastAPI(
        title=settings.app_name,
        description="Multi-agent IT operations investigation and incident diagnosis platform.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")

    init_db()

    return app


app = create_app()
