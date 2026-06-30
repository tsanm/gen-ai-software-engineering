"""Shared pytest fixtures for the pipeline test-suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def base_txn() -> dict[str, Any]:
    """A clean, valid transaction record used as a starting point in tests."""

    return {
        "transaction_id": "TXN999",
        "timestamp": "2026-03-16T12:00:00Z",
        "source_account": "ACC-1000",
        "destination_account": "ACC-2000",
        "amount": "100.00",
        "currency": "USD",
        "transaction_type": "transfer",
        "description": "unit test",
        "metadata": {"channel": "online", "country": "US"},
    }


@pytest.fixture
def sample_path(tmp_path: Path) -> Path:
    """Write a small sample-transactions.json into an isolated temp dir."""

    records = [
        {
            "transaction_id": "TXN001",
            "timestamp": "2026-03-16T12:00:00Z",
            "source_account": "ACC-1001",
            "destination_account": "ACC-2001",
            "amount": "100.00",
            "currency": "USD",
            "transaction_type": "transfer",
            "description": "ok",
            "metadata": {"channel": "online", "country": "US"},
        },
        {
            "transaction_id": "TXN002",
            "timestamp": "2026-03-16T12:05:00Z",
            "source_account": "ACC-1002",
            "destination_account": "ACC-9999",
            "amount": "20000.00",
            "currency": "USD",
            "transaction_type": "wire_transfer",
            "description": "blocked dest",
            "metadata": {"channel": "branch", "country": "US"},
        },
        {
            "transaction_id": "TXN003",
            "timestamp": "2026-03-16T12:10:00Z",
            "source_account": "ACC-1003",
            "destination_account": "ACC-3003",
            "amount": "10.00",
            "currency": "XYZ",
            "transaction_type": "transfer",
            "description": "bad currency",
            "metadata": {"channel": "online", "country": "US"},
        },
    ]
    path = tmp_path / "sample-transactions.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path
