"""FastAPI dependencies that expose per-app state (store, audit, region, settings)."""
from __future__ import annotations

from fastapi import Request

from src.compliance import AuditLog, CompliancePolicy
from src.config import Settings
from src.regions import Region
from src.store import TransactionStore


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
