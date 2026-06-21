"""Agent 5 of the pipeline: the Reporting Agent.

Terminal agent. It writes each transaction's final record into
``shared/results/`` and, once the whole run is done, produces a roll-up
summary (counts by status, totals settled per currency, flagged/rejected
transactions with reasons). The summary is the artefact the custom MCP
``pipeline://summary`` resource exposes.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from agents.common import Message, iso_now, parse_money

AGENT_NAME = "reporting_agent"


def finalize(record: dict[str, Any]) -> dict[str, Any]:
    """Stamp a record as finalised for persistence in ``shared/results/``."""

    return {**record, "finalized_at": iso_now()}


def process_message(message: dict[str, Any]) -> dict[str, Any]:
    """Finalise the inbound transaction record (terminal step)."""

    inbound = Message.from_dict(message)
    final = finalize(inbound.data)
    outbound = Message(
        source_agent=AGENT_NAME,
        target_agent="results",
        message_type="result",
        data=final,
    )
    return outbound.to_dict()


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the run summary from the list of finalised transaction records."""

    by_status: dict[str, int] = defaultdict(int)
    settled_totals: dict[str, str] = {}
    settled_acc: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    flagged: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for record in results:
        status = str(record.get("status", "unknown"))
        by_status[status] += 1

        if status == "settled":
            currency = str(record.get("currency", "USD"))
            settled_acc[currency] += parse_money(record.get("net_amount", "0"))
        if record.get("risk_band") == "high":
            flagged.append(
                {
                    "transaction_id": record.get("transaction_id"),
                    "risk_score": record.get("risk_score"),
                    "reasons": record.get("risk_reasons", []),
                }
            )
        if status == "rejected":
            rejected.append(
                {
                    "transaction_id": record.get("transaction_id"),
                    "reason": record.get("reason", "unspecified"),
                }
            )

    settled_totals = {cur: str(total) for cur, total in sorted(settled_acc.items())}

    return {
        "generated_at": iso_now(),
        "total_transactions": len(results),
        "by_status": dict(sorted(by_status.items())),
        "settled_totals_by_currency": settled_totals,
        "flagged_for_review": flagged,
        "rejected": rejected,
    }


def render_summary_text(summary: dict[str, Any]) -> str:
    """Render the summary dict as a human-readable text report."""

    lines = [
        "=== Pipeline Run Summary ===",
        f"generated_at: {summary['generated_at']}",
        f"total_transactions: {summary['total_transactions']}",
        "",
        "by_status:",
    ]
    for status, count in summary["by_status"].items():
        lines.append(f"  {status}: {count}")
    lines.append("")
    lines.append("settled_totals_by_currency:")
    for currency, total in summary["settled_totals_by_currency"].items():
        lines.append(f"  {currency}: {total}")
    lines.append("")
    lines.append(f"flagged_for_review: {len(summary['flagged_for_review'])}")
    for item in summary["flagged_for_review"]:
        lines.append(
            f"  {item['transaction_id']} score={item['risk_score']} "
            f"reasons={','.join(item['reasons'])}"
        )
    lines.append("")
    lines.append(f"rejected: {len(summary['rejected'])}")
    for item in summary["rejected"]:
        lines.append(f"  {item['transaction_id']} reason={item['reason']}")
    return "\n".join(lines) + "\n"


def write_summary(summary: dict[str, Any], results_dir: Path) -> tuple[Path, Path]:
    """Write the summary as both JSON and text; return (json_path, text_path)."""

    import json

    json_path = results_dir / "_summary.json"
    text_path = results_dir / "_summary.txt"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    text_path.write_text(render_summary_text(summary), encoding="utf-8")
    return json_path, text_path
