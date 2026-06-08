"""Shared pytest fixtures.

Every test builds its own FastAPI app via the factory, giving each test a fresh
in-memory store and services (full isolation, no shared state).
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"


def make_settings(**overrides) -> Settings:
    base = dict(max_import_records=1000, max_import_bytes=5_000_000, log_level="WARNING")
    base.update(overrides)
    return Settings(**base)


# raise_server_exceptions=False so we can assert on the 500 response our handler
# returns, instead of TestClient re-raising the underlying exception.
@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(make_settings()), raise_server_exceptions=False)


@pytest.fixture
def make_client():
    def _make(**overrides) -> TestClient:
        return TestClient(create_app(make_settings(**overrides)),
                          raise_server_exceptions=False)

    return _make


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


# --- payload helpers -------------------------------------------------------

def ticket(**over) -> dict:
    """A valid ticket-create payload; override any field via kwargs."""
    payload = dict(
        customer_id="CUST-1",
        customer_email="user@example.com",
        customer_name="Jane Doe",
        subject="Cannot log in",
        description="I cannot log in to my account after the latest update.",
        metadata=dict(source="web_form", browser="Chrome", device_type="desktop"),
    )
    payload.update(over)
    return payload


def create(client, payload=None) -> dict:
    """POST a ticket, assert acceptance, return the created body."""
    r = client.post("/tickets", json=payload if payload is not None else ticket())
    assert r.status_code == 201, r.text
    return r.json()


def import_bytes(client, filename, content, fmt=None, auto_classify=False):
    """POST a file to /tickets/import; return the raw response."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    params: dict = {}
    if fmt is not None:
        params["format"] = fmt
    if auto_classify:
        params["auto_classify"] = "true"
    return client.post(
        "/tickets/import",
        files={"file": (filename, content, "application/octet-stream")},
        params=params)
