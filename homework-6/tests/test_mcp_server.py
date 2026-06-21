"""Unit tests for the custom FastMCP pipeline-status server.

The server module is loaded by path because the ``mcp/`` directory is not a
Python package (it would otherwise shadow the installed ``mcp`` library).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from agents.common import configure_audit_logger
from integrator import run_pipeline

_SERVER_PATH = Path(__file__).resolve().parent.parent / "mcp" / "server.py"


def _load_server() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pipeline_mcp_server", _SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def server_with_results(
    sample_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> ModuleType:
    shared = tmp_path / "shared"
    run_pipeline(sample_path, shared, configure_audit_logger(tmp_path / "a.log"))
    module = _load_server()
    results_dir = shared / "results"
    monkeypatch.setattr(module, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(module, "SUMMARY_TEXT", results_dir / "_summary.txt")
    monkeypatch.setattr(module, "SUMMARY_JSON", results_dir / "_summary.json")
    return module


def test_get_transaction_status_found(server_with_results: ModuleType) -> None:
    status = server_with_results.get_transaction_status_impl("TXN001")
    assert status["transaction_id"] == "TXN001"
    assert status["status"] == "settled"
    # PII-safe: account is masked.
    assert status["source_account"].startswith("****")


def test_get_transaction_status_not_found(server_with_results: ModuleType) -> None:
    status = server_with_results.get_transaction_status_impl("NOPE")
    assert status["status"] == "not_found"


def test_list_pipeline_results(server_with_results: ModuleType) -> None:
    listing = server_with_results.list_pipeline_results_impl()
    assert listing["count"] == 3
    ids = {r["transaction_id"] for r in listing["results"]}
    assert ids == {"TXN001", "TXN002", "TXN003"}


def test_pipeline_summary_resource(server_with_results: ModuleType) -> None:
    text = server_with_results.pipeline_summary_impl()
    assert "Pipeline Run Summary" in text


def test_pipeline_summary_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_server()
    monkeypatch.setattr(module, "SUMMARY_TEXT", tmp_path / "nope.txt")
    monkeypatch.setattr(module, "SUMMARY_JSON", tmp_path / "nope.json")
    assert "No pipeline summary" in module.pipeline_summary_impl()


def test_build_server_registers_tools() -> None:
    module = _load_server()
    server = module.build_server()
    assert server.name == "pipeline-status"


def test_summary_json_fallback(
    server_with_results: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Remove the text summary so the JSON fallback path is exercised.
    monkeypatch.setattr(server_with_results, "SUMMARY_TEXT", Path("/nonexistent/x.txt"))
    text = server_with_results.pipeline_summary_impl()
    json.loads(text)  # must be valid JSON
