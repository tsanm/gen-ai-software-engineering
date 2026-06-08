"""Application factory and cross-cutting wiring.

``create_app(settings)`` builds a fully isolated app: its own store and services live on
``app.state``, so each test gets fresh state and there are no module-level globals. Every
response carries an ``X-Request-ID`` and every failure renders through one error envelope.
"""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import Settings
from src.errors import ApiError, error_body
from src.models import TicketStore
from src.routes import tickets
from src.services import ImportService, TicketService

logger = logging.getLogger("support_api")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    app = FastAPI(
        title="Intelligent Customer Support API",
        version="1.0.0",
        description="Homework 2 - in-memory customer support ticket system")

    # --- per-app state ---
    store = TicketStore()
    ticket_service = TicketService(store)
    app.state.settings = settings
    app.state.store = store
    app.state.ticket_service = ticket_service
    app.state.import_service = ImportService(
        ticket_service,
        max_records=settings.max_import_records,
        max_bytes=settings.max_import_bytes)

    _register_middleware(app)
    _register_exception_handlers(app)
    app.include_router(tickets.router)

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/", tags=["ops"])
    def root() -> dict:
        return {"name": "Intelligent Customer Support API",
                "docs": "/docs", "health": "/health"}

    return app


def _register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def observe(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info("%s %s -> %d (%.1fms) rid=%s", request.method,
                    request.url.path, response.status_code, duration_ms, request_id)
        return response


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError):
        rid = getattr(request.state, "request_id", None)
        return _envelope(exc.status_code, exc.error, rid, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", None)
        details = [
            {"field": _field_from_loc(err.get("loc", ())), "message": err.get("msg", "Invalid")}
            for err in exc.errors()
        ]
        return _envelope(400, "Validation failed", rid, details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        rid = getattr(request.state, "request_id", None)
        return _envelope(exc.status_code, str(exc.detail), rid)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        rid = getattr(request.state, "request_id", None)
        logger.exception("unhandled error rid=%s", rid)  # full detail to logs only
        return _envelope(500, "Internal server error", rid)


def _envelope(status_code: int, error: str, request_id: str | None,
              details: list[dict] | None = None) -> JSONResponse:
    resp = JSONResponse(status_code=status_code,
                        content=error_body(error, request_id, details))
    if request_id:
        resp.headers["X-Request-ID"] = request_id
    return resp


def _field_from_loc(loc) -> str | None:
    """Pick the user-facing field name from a Pydantic error location tuple."""
    parts = [p for p in loc if p not in ("body", "query", "path")]
    return str(parts[-1]) if parts else None


# Module-level app for `uvicorn src.main:app`.
app = create_app()
