"""FastAPI dependency providers (web-layer wiring).

Expose per-app state (store, audit, region, settings) and assemble the application
services that the routes depend on, so route handlers never construct services by hand.
"""
from __future__ import annotations

from fastapi import Request

from src.config import Settings
from src.models.store import TransactionStore
from src.services import AccountService, TransactionService
from src.services.compliance import AuditLog, CompliancePolicy
from src.services.regions import Region


def get_store(request: Request) -> TransactionStore:
    return request.app.state.store


def get_audit(request: Request) -> AuditLog:
    return request.app.state.audit


def get_region(request: Request) -> Region:
    return request.app.state.region


def get_policy(request: Request) -> CompliancePolicy:
    return request.app.state.policy


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def get_account_service(request: Request) -> AccountService:
    state = request.app.state
    return AccountService(state.store, state.region)


def get_transaction_service(request: Request) -> TransactionService:
    state = request.app.state
    return TransactionService(
        state.store, state.region, state.audit, state.policy, get_request_id(request))
