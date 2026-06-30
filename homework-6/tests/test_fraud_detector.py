"""Unit tests for the fraud detector agent."""

from __future__ import annotations

from typing import Any

from agents import fraud_detector as fd
from agents.common import Message


def test_low_value_domestic_is_low_risk(base_txn: dict[str, Any]) -> None:
    result = fd.score_transaction(base_txn)
    assert result["risk_band"] == "low"
    assert result["status"] == "passed_fraud"
    assert result["risk_score"] < 25


def test_very_high_value_flagged(base_txn: dict[str, Any]) -> None:
    base_txn["amount"] = "75000.00"
    result = fd.score_transaction(base_txn)
    assert result["status"] == "fraud_review"
    assert result["risk_band"] == "high"
    assert "high_value>=50000" in result["risk_reasons"]


def test_mid_value_band(base_txn: dict[str, Any]) -> None:
    base_txn["amount"] = "12000.00"
    result = fd.score_transaction(base_txn)
    assert result["risk_score"] >= 25


def test_off_hours_adds_points(base_txn: dict[str, Any]) -> None:
    base_txn["timestamp"] = "2026-03-16T02:30:00Z"
    result = fd.score_transaction(base_txn)
    assert "off_hours" in result["risk_reasons"]


def test_cross_border_adds_points(base_txn: dict[str, Any]) -> None:
    base_txn["metadata"]["country"] = "DE"
    result = fd.score_transaction(base_txn)
    assert any(r.startswith("cross_border") for r in result["risk_reasons"])


def test_wire_transfer_adds_points(base_txn: dict[str, Any]) -> None:
    base_txn["transaction_type"] = "wire_transfer"
    result = fd.score_transaction(base_txn)
    assert "wire_transfer" in result["risk_reasons"]


def test_score_capped_at_100(base_txn: dict[str, Any]) -> None:
    base_txn["amount"] = "75000.00"
    base_txn["transaction_type"] = "wire_transfer"
    base_txn["timestamp"] = "2026-03-16T03:00:00Z"
    base_txn["metadata"]["country"] = "DE"
    result = fd.score_transaction(base_txn)
    assert result["risk_score"] <= 100


def test_bad_timestamp_no_off_hours(base_txn: dict[str, Any]) -> None:
    base_txn["timestamp"] = "not-a-date"
    result = fd.score_transaction(base_txn)
    assert "off_hours" not in result["risk_reasons"]


def test_process_message_targets_compliance(base_txn: dict[str, Any]) -> None:
    msg = Message("transaction_validator", "fraud_detector", "transaction", base_txn)
    out = fd.process_message(msg.to_dict())
    assert out["target_agent"] == "compliance_checker"
    assert "risk_score" in out["data"]
