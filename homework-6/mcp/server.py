"""Custom FastMCP server exposing the banking pipeline state.

Run as a standalone script (``python mcp/server.py``) so the directory name
``mcp`` does not shadow the installed ``mcp`` library on ``sys.path``.

Exposed capabilities (per the specification):

* Tool ``get_transaction_status(transaction_id)`` -- current status and key
  fields for a single transaction, read from ``shared/results/``.
* Tool ``list_pipeline_results()`` -- a summary of every processed transaction.
* Resource ``pipeline://summary`` -- the latest run summary as text.

All reads are PII-safe: account numbers are masked before being returned.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Make the homework root importable when run as ``python mcp/server.py``.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agents.common import mask_account  # noqa: E402

try:  # pragma: no cover - import shim for both run styles
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment,misc]

RESULTS_DIR = _ROOT / "shared" / "results"
SUMMARY_TEXT = RESULTS_DIR / "_summary.txt"
SUMMARY_JSON = RESULTS_DIR / "_summary.json"

SAFE_FIELDS = (
    "transaction_id",
    "status",
    "currency",
    "amount",
    "net_amount",
    "fee",
    "risk_score",
    "risk_band",
    "compliance_decision",
    "settlement_status",
    "reason",
)


def _safe_view(record: dict[str, Any]) -> dict[str, Any]:
    """Return a PII-safe projection of a result record."""

    view = {k: record[k] for k in SAFE_FIELDS if k in record}
    if "source_account" in record:
        view["source_account"] = mask_account(str(record["source_account"]))
    if "destination_account" in record:
        view["destination_account"] = mask_account(str(record["destination_account"]))
    return view


def _load_result(transaction_id: str) -> dict[str, Any] | None:
    path = RESULTS_DIR / f"{transaction_id}.json"
    if not path.exists():
        return None
    envelope = json.loads(path.read_text(encoding="utf-8"))
    record: dict[str, Any] = envelope.get("data", envelope)
    return record


def get_transaction_status_impl(transaction_id: str) -> dict[str, Any]:
    """Implementation of the ``get_transaction_status`` tool (testable)."""

    record = _load_result(transaction_id)
    if record is None:
        return {"transaction_id": transaction_id, "status": "not_found"}
    return _safe_view(record)


def list_pipeline_results_impl() -> dict[str, Any]:
    """Implementation of the ``list_pipeline_results`` tool (testable)."""

    results: list[dict[str, Any]] = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        envelope = json.loads(path.read_text(encoding="utf-8"))
        record = envelope.get("data", envelope)
        results.append(_safe_view(record))
    return {"count": len(results), "results": results}


def pipeline_summary_impl() -> str:
    """Implementation of the ``pipeline://summary`` resource (testable)."""

    if SUMMARY_TEXT.exists():
        return SUMMARY_TEXT.read_text(encoding="utf-8")
    if SUMMARY_JSON.exists():
        return SUMMARY_JSON.read_text(encoding="utf-8")
    return "No pipeline summary available. Run: python integrator.py"


def build_server() -> Any:
    """Construct and return the configured FastMCP server instance."""

    if FastMCP is None:  # pragma: no cover - exercised only without fastmcp
        raise RuntimeError("fastmcp is not installed")

    server = FastMCP("pipeline-status")

    @server.tool
    def get_transaction_status(transaction_id: str) -> dict[str, Any]:
        """Return the current pipeline status for a single transaction."""

        return get_transaction_status_impl(transaction_id)

    @server.tool
    def list_pipeline_results() -> dict[str, Any]:
        """Return a PII-safe summary of every processed transaction."""

        return list_pipeline_results_impl()

    @server.resource("pipeline://summary")
    def pipeline_summary() -> str:
        """Return the latest pipeline run summary as text."""

        return pipeline_summary_impl()

    return server


def main() -> None:  # pragma: no cover - process entry point
    """Start the FastMCP server over stdio."""

    build_server().run()


if __name__ == "__main__":  # pragma: no cover - CLI shim
    main()
