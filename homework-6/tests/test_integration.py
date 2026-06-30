"""End-to-end integration tests for the full pipeline.

These tests run the integrator against an isolated ``shared/`` directory under
``tmp_path`` so they never touch the repository's real shared state.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.common import configure_audit_logger
from integrator import load_transactions, run_pipeline


def test_full_pipeline_processes_every_transaction(sample_path: Path, tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    logger = configure_audit_logger(tmp_path / "audit.log")
    summary = run_pipeline(sample_path, shared, logger)

    expected = {r["transaction_id"] for r in load_transactions(sample_path)}
    written = {p.stem for p in (shared / "results").glob("*.json") if not p.name.startswith("_")}

    assert written == expected
    assert summary["all_processed"] is True
    assert summary["missing"] == []
    assert summary["total_transactions"] == len(expected)


def test_pipeline_outcomes(sample_path: Path, tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    run_pipeline(sample_path, shared, configure_audit_logger(tmp_path / "a.log"))

    def status(txn: str) -> str:
        envelope = json.loads((shared / "results" / f"{txn}.json").read_text(encoding="utf-8"))
        return str(envelope["data"]["status"])

    assert status("TXN001") == "settled"  # clean
    assert status("TXN002") == "rejected"  # blocked destination ACC-9999
    assert status("TXN003") == "rejected"  # currency XYZ


def test_results_are_pii_safe(sample_path: Path, tmp_path: Path) -> None:
    """Audit log must not contain raw account numbers."""

    shared = tmp_path / "shared"
    audit_log = tmp_path / "audit.log"
    run_pipeline(sample_path, shared, configure_audit_logger(audit_log))
    content = audit_log.read_text(encoding="utf-8")
    assert "ACC-1001" not in content
    assert "ACC-9999" not in content
    assert "****" in content


def test_summary_files_written(sample_path: Path, tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    run_pipeline(sample_path, shared, configure_audit_logger(tmp_path / "a.log"))
    assert (shared / "results" / "_summary.json").exists()
    assert (shared / "results" / "_summary.txt").exists()


def test_run_capture_is_immutable_and_complete(sample_path: Path, tmp_path: Path) -> None:
    """Each run writes a timestamped capture with results, audit log + manifest."""

    shared = tmp_path / "shared"
    summary = run_pipeline(sample_path, shared, configure_audit_logger(tmp_path / "a.log"))

    run_dir = Path(summary["run_dir"])
    assert run_dir.parent == shared / "runs"
    assert run_dir.name.startswith("run-")

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == run_dir.name
    assert manifest["config"] == "pipeline.config.json"
    assert manifest["all_processed"] is True

    expected = {r["transaction_id"] for r in load_transactions(sample_path)}
    captured = {p.stem for p in (run_dir / "results").glob("*.json") if not p.name.startswith("_")}
    assert captured == expected

    audit = (run_dir / "audit.log").read_text(encoding="utf-8")
    assert "ACC-1001" not in audit and "****" in audit


def test_run_captures_are_distinct_per_run(sample_path: Path, tmp_path: Path) -> None:
    """A second run never overwrites the first (immutable evidence trail)."""

    shared = tmp_path / "shared"
    logger = configure_audit_logger(tmp_path / "a.log")
    first = run_pipeline(sample_path, shared, logger)
    # Force a distinct timestamp without sleeping.
    import integrator as integ

    monkey = "2026-01-01T00-00-00Z"
    orig = integ._run_stamp
    integ._run_stamp = lambda: monkey  # type: ignore[assignment]
    try:
        second = run_pipeline(sample_path, shared, logger)
    finally:
        integ._run_stamp = orig  # type: ignore[assignment]

    assert first["run_dir"] != second["run_dir"]
    assert len(list((shared / "runs").glob("run-*"))) == 2


def test_message_protocol_shape(sample_path: Path, tmp_path: Path) -> None:
    """Every result file must be a valid standard message envelope."""

    shared = tmp_path / "shared"
    run_pipeline(sample_path, shared, configure_audit_logger(tmp_path / "a.log"))
    for path in (shared / "results").glob("*.json"):
        if path.name.startswith("_"):
            continue
        envelope = json.loads(path.read_text(encoding="utf-8"))
        for key in (
            "message_id",
            "timestamp",
            "source_agent",
            "target_agent",
            "message_type",
            "data",
        ):
            assert key in envelope
