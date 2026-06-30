"""Integrator / orchestrator for the multi-agent banking pipeline.

Responsibilities (per the specification):

1. Create the ``shared/{input,processing,output,results}`` directories.
2. Load ``sample-transactions.json`` and drop one envelope per transaction
   into ``shared/input/``.
3. Run the cooperating agents **in order**, passing each transaction through
   the file-based JSON message protocol:

       validator -> fraud_detector -> compliance_checker
                 -> settlement_processor -> reporting_agent

   Rejected/held transactions short-circuit to the reporting agent so every
   transaction reaches a terminal state.
4. Persist each final record to ``shared/results/`` and write a run summary.
5. Monitor results and confirm every input transaction was processed.

Run with::

    python integrator.py
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agents import (
    compliance_checker,
    fraud_detector,
    reporting_agent,
    settlement_processor,
    transaction_validator,
)
from agents.common import (
    Message,
    PipelinePaths,
    audit,
    configure_audit_logger,
    iso_now,
    load_config,
    mask_account,
)

ProcessFn = Callable[[dict[str, Any]], dict[str, Any]]

_CONFIG: dict[str, Any] = load_config()

#: Ordered chain of agent stages, sourced from ``pipeline.config.json`` so the
#: order can be changed without touching code.
STAGE_ORDER: tuple[str, ...] = tuple(_CONFIG["stage_order"])

STAGE_FUNCS: dict[str, ProcessFn] = {
    "transaction_validator": transaction_validator.process_message,
    "fraud_detector": fraud_detector.process_message,
    "compliance_checker": compliance_checker.process_message,
    "settlement_processor": settlement_processor.process_message,
    "reporting_agent": reporting_agent.process_message,
}

#: Terminal statuses that should skip straight to reporting (no settlement),
#: sourced from config.
SHORT_CIRCUIT_STATUSES: set[str] = set(_CONFIG["short_circuit_statuses"])


def load_transactions(sample_path: Path) -> list[dict[str, Any]]:
    """Load raw transaction records from ``sample_path``."""

    data = json.loads(sample_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("sample-transactions.json must contain a JSON array")
    return data


def seed_input(records: list[dict[str, Any]], paths: PipelinePaths) -> None:
    """Drop one initial envelope per transaction into ``shared/input/``."""

    for record in records:
        message = Message(
            source_agent="integrator",
            target_agent="transaction_validator",
            message_type="transaction",
            data=record,
        )
        message.write(paths.input)


def _route(stage: str, data: dict[str, Any]) -> str:
    """Determine the next stage for a record leaving ``stage``.

    The reporting agent is always terminal. Records that reach a terminal
    status mid-chain (e.g. rejected at validation/compliance) jump straight to
    the reporting agent instead of continuing through settlement.
    """

    idx = STAGE_ORDER.index(stage)
    if stage == "reporting_agent":
        return "done"

    status = str(data.get("status", ""))
    reporting_idx = STAGE_ORDER.index("reporting_agent")
    if status in SHORT_CIRCUIT_STATUSES and idx < reporting_idx:
        return "reporting_agent"
    return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else "done"


def process_one(
    record: dict[str, Any],
    paths: PipelinePaths,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Run a single transaction through every agent stage in order.

    Each hop writes the working envelope to ``shared/processing`` (in-flight)
    and the produced envelope to ``shared/output`` (hand-off), mirroring the
    file-based protocol, before the final record lands in ``shared/results``.
    """

    txn_id = str(record.get("transaction_id", "?"))
    envelope = Message(
        source_agent="integrator",
        target_agent="transaction_validator",
        message_type="transaction",
        data=record,
    ).to_dict()

    stage: str = "transaction_validator"
    while stage != "done":
        Message.from_dict(envelope).write(paths.processing, name=f"{txn_id}.json")
        envelope = STAGE_FUNCS[stage](envelope)
        Message.from_dict(envelope).write(paths.output, name=f"{txn_id}.json")
        data = envelope["data"]
        audit(
            logger,
            stage,
            txn_id,
            str(data.get("status", "unknown")),
            detail=f"src={mask_account(str(data.get('source_account', '')))}",
        )
        stage = _route(stage, data)

    final = reporting_agent.finalize(envelope["data"])
    Message(
        source_agent="reporting_agent",
        target_agent="results",
        message_type="result",
        data=final,
    ).write(paths.results, name=f"{txn_id}.json")
    return final


def _run_stamp() -> str:
    """Return a filesystem-safe UTC run stamp, e.g. ``2026-06-22T10-30-00Z``."""

    return iso_now().replace(":", "-")


def capture_run(
    run_stamp: str,
    shared_root: Path,
    paths: PipelinePaths,
    finals: list[dict[str, Any]],
    summary: dict[str, Any],
) -> Path:
    """Write an immutable, timestamped capture of this run under ``shared/runs/``.

    The capture contains a copy of every finalised per-transaction result, the
    run summary (json + text), a structured audit log scoped to this run, and a
    ``manifest.json`` describing the run. ``shared/results/`` continues to hold
    the latest run as a convenient pointer; the run folder is the evidence trail
    and is never overwritten.
    """

    run_dir = shared_root / "runs" / f"run-{run_stamp}"
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    audit_lines: list[str] = []
    for final in finals:
        txn_id = str(final.get("transaction_id", "?"))
        Message(
            source_agent="reporting_agent",
            target_agent="results",
            message_type="result",
            data=final,
        ).write(results_dir, name=f"{txn_id}.json")
        audit_lines.append(
            f"{iso_now()} agent=reporting_agent txn={txn_id} "
            f"outcome={final.get('status', 'unknown')} "
            f"detail=src={mask_account(str(final.get('source_account', '')))}"
        )

    reporting_agent.write_summary(summary, results_dir)
    (run_dir / "audit.log").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    manifest = {
        "run_id": f"run-{run_stamp}",
        "generated_at": summary.get("generated_at"),
        "config": "pipeline.config.json",
        "stage_order": list(STAGE_ORDER),
        "total_transactions": summary.get("total_transactions"),
        "by_status": summary.get("by_status"),
        "all_processed": summary.get("all_processed"),
        "artifacts": ["results/", "audit.log", "results/_summary.json", "results/_summary.txt"],
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_dir


def run_pipeline(
    sample_path: Path,
    shared_root: Path,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Run the full pipeline end-to-end and return the run summary dict."""

    logger = logger or configure_audit_logger(shared_root / "audit.log")
    paths = PipelinePaths.create(shared_root)
    run_stamp = _run_stamp()

    records = load_transactions(sample_path)
    seed_input(records, paths)
    audit(logger, "integrator", "*", "loaded", detail=f"count={len(records)}")

    finals: list[dict[str, Any]] = [process_one(record, paths, logger) for record in records]

    summary = reporting_agent.build_summary(finals)
    reporting_agent.write_summary(summary, paths.results)

    processed_ids = {str(r.get("transaction_id")) for r in finals}
    expected_ids = {str(r.get("transaction_id")) for r in records}
    missing = expected_ids - processed_ids
    audit(
        logger,
        "integrator",
        "*",
        "complete" if not missing else "incomplete",
        detail=f"processed={len(processed_ids)} missing={sorted(missing)}",
    )
    summary["all_processed"] = not missing
    summary["missing"] = sorted(missing)

    run_dir = capture_run(run_stamp, shared_root, paths, finals, summary)
    summary["run_dir"] = str(run_dir)
    audit(logger, "integrator", "*", "captured", detail=f"run={run_dir.name}")
    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for ``python integrator.py``."""

    here = Path(__file__).resolve().parent
    sample_path = here / "sample-transactions.json"
    shared_root = here / "shared"

    logger = configure_audit_logger(shared_root / "audit.log")
    summary = run_pipeline(sample_path, shared_root, logger)

    print(reporting_agent.render_summary_text(summary))
    print(f"Results written to: {shared_root / 'results'}")
    print(f"Run captured to:    {summary.get('run_dir')}")
    if summary["all_processed"]:
        print(f"OK: all {summary['total_transactions']} transactions appear in shared/results/")
        return 0
    print(f"ERROR: missing transactions: {summary['missing']}")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI shim
    sys.exit(main())
