"""Unit tests for the reporting agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents import reporting_agent as ra
from agents.common import Message


def _record(**kw: Any) -> dict[str, Any]:
    base = {
        "transaction_id": "T",
        "currency": "USD",
        "status": "settled",
        "net_amount": "100.00",
    }
    base.update(kw)
    return base


def test_finalize_stamps_time(base_txn: dict[str, Any]) -> None:
    result = ra.finalize(base_txn)
    assert "finalized_at" in result


def test_build_summary_counts() -> None:
    results = [
        _record(transaction_id="A", status="settled", net_amount="100.00"),
        _record(transaction_id="B", status="settled", net_amount="50.00"),
        _record(transaction_id="C", status="rejected", reason="bad"),
    ]
    summary = ra.build_summary(results)
    assert summary["total_transactions"] == 3
    assert summary["by_status"]["settled"] == 2
    assert summary["settled_totals_by_currency"]["USD"] == "150.00"
    assert summary["rejected"][0]["transaction_id"] == "C"


def test_build_summary_flags_high_risk() -> None:
    results = [
        _record(
            transaction_id="H",
            status="held",
            risk_band="high",
            risk_score=80,
            risk_reasons=["high_value>=50000"],
        )
    ]
    summary = ra.build_summary(results)
    assert summary["flagged_for_review"][0]["transaction_id"] == "H"


def test_render_summary_text() -> None:
    summary = ra.build_summary([_record(transaction_id="A")])
    text = ra.render_summary_text(summary)
    assert "Pipeline Run Summary" in text
    assert "by_status" in text


def test_render_summary_text_with_flagged_and_rejected() -> None:
    results = [
        _record(
            transaction_id="H",
            status="held",
            risk_band="high",
            risk_score=80,
            risk_reasons=["high_value>=50000", "wire_transfer"],
        ),
        _record(transaction_id="R", status="rejected", reason="blocked"),
    ]
    text = ra.render_summary_text(ra.build_summary(results))
    assert "H score=80" in text
    assert "R reason=blocked" in text


def test_write_summary(tmp_path: Path) -> None:
    summary = ra.build_summary([_record(transaction_id="A")])
    json_path, text_path = ra.write_summary(summary, tmp_path)
    assert json_path.exists() and text_path.exists()
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["total_transactions"] == 1


def test_process_message_targets_results(base_txn: dict[str, Any]) -> None:
    msg = Message("settlement_processor", "reporting_agent", "transaction", base_txn)
    out = ra.process_message(msg.to_dict())
    assert out["target_agent"] == "results"
    assert out["message_type"] == "result"
