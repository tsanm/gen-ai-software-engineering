"""Shared pytest fixtures.

Every test builds its own FastAPI app via the factory, giving each test a fresh
in-memory store, audit log, and rate-limiter (full isolation, no shared state).
"""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import create_app


def make_settings(**overrides) -> Settings:
    base = dict(
        region="DEFAULT",
        rate_limit_max=100,
        rate_limit_window_seconds=60,
        large_amount_threshold=Decimal("10000"),
        log_level="WARNING",
    )
    base.update(overrides)
    return Settings(**base)


# raise_server_exceptions=False so we can assert on the 500 response our handler
# returns, instead of TestClient re-raising the underlying exception.
@pytest.fixture
def client() -> TestClient:
    """Default client with spec-default settings."""
    return TestClient(create_app(make_settings()), raise_server_exceptions=False)


@pytest.fixture
def make_client():
    """Factory so a test can spin up a client with custom settings (region, limits)."""
    def _make(**overrides) -> TestClient:
        return TestClient(create_app(make_settings(**overrides)),
                          raise_server_exceptions=False)

    return _make


# --- payload helpers -------------------------------------------------------

def transfer(**over):
    p = dict(fromAccount="ACC-12345", toAccount="ACC-67890", amount=100.50,
             currency="USD", type="transfer")
    p.update(over)
    return p


def deposit(**over):
    p = dict(toAccount="ACC-12345", amount=200.00, currency="USD", type="deposit")
    p.update(over)
    return p


def withdrawal(**over):
    p = dict(fromAccount="ACC-12345", amount=50.00, currency="USD", type="withdrawal")
    p.update(over)
    return p


def create(client, payload):
    """POST a transaction and assert it was accepted, returning the body."""
    r = client.post("/transactions", json=payload)
    assert r.status_code == 201, r.text
    return r.json()
