"""Application factory and cross-cutting wiring.

`create_app(settings)` builds a fully isolated app: its own store, audit log, region,
compliance policy, and rate limiter live on `app.state`. This makes the app both
test-friendly (fresh state per test) and free of module-level globals.
"""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.compliance import AuditLog, CompliancePolicy
from src.config import Settings
from src.errors import ApiError, error_body
from src.rate_limit import RateLimiter
from src.regions import get_region
from src.routers import accounts, transactions
from src.store import TransactionStore

logger = logging.getLogger("banking_api")

# Paths that should never be rate-limited (operability / docs).
RATE_LIMIT_EXEMPT = {"/health", "/docs", "/redoc", "/openapi.json"}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    app = FastAPI(title="Banking Transactions API", version="1.0.0",
                  description="Homework 1 - in-memory banking transactions API")

    # --- per-app state ---
    app.state.settings = settings
    app.state.store = TransactionStore()
    app.state.audit = AuditLog()
    app.state.region = get_region(settings.region)
    app.state.policy = CompliancePolicy(settings.large_amount_threshold)
    app.state.rate_limiter = RateLimiter(
        settings.rate_limit_max, settings.rate_limit_window_seconds)

    _register_middleware(app)
    _register_exception_handlers(app)

    app.include_router(transactions.router)
    app.include_router(accounts.router)

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok", "region": settings.region}

    @app.get("/", tags=["ops"])
    def root() -> dict:
        return {"name": "Banking Transactions API", "docs": "/docs", "health": "/health"}

    return app


def _register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def observe_and_limit(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Rate limiting (Task 4-D), skipping ops/docs endpoints.
        if request.url.path not in RATE_LIMIT_EXEMPT:
            limiter: RateLimiter = request.app.state.rate_limiter
            client_ip = request.client.host if request.client else "unknown"
            if not limiter.allow(client_ip, time.monotonic()):
                logger.warning("rate_limited ip=%s path=%s rid=%s",
                               client_ip, request.url.path, request_id)
                resp = JSONResponse(
                    status_code=429,
                    content=error_body("Too Many Requests", request_id,
                                       [{"field": None, "message":
                                         "Rate limit exceeded. Try again later."}]))
                resp.headers["X-Request-ID"] = request_id
                return resp

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
        resp = JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.error, rid, exc.details))
        if rid:
            resp.headers["X-Request-ID"] = rid
        return resp

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", None)
        details = [
            {"field": _field_from_loc(err.get("loc", ())), "message": err.get("msg", "Invalid")}
            for err in exc.errors()
        ]
        resp = JSONResponse(
            status_code=400,
            content=error_body("Validation failed", rid, details))
        if rid:
            resp.headers["X-Request-ID"] = rid
        return resp

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        rid = getattr(request.state, "request_id", None)
        logger.exception("unhandled error rid=%s", rid)  # full detail to logs only
        resp = JSONResponse(
            status_code=500,
            content=error_body("Internal server error", rid))
        if rid:
            resp.headers["X-Request-ID"] = rid
        return resp


def _field_from_loc(loc) -> str | None:
    """Pick the user-facing field name from a Pydantic error location tuple."""
    parts = [p for p in loc if p not in ("body", "query", "path")]
    return str(parts[-1]) if parts else None


# Module-level app for `uvicorn src.main:app`.
app = create_app()
