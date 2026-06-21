"""Unit tests for the compliance checker agent."""

from __future__ import annotations

from typing import Any

from agents import compliance_checker as cc
from agents.common import Message


def test_approved_when_clean(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "passed_fraud"
    result = cc.check_compliance(base_txn)
    assert result["compliance_decision"] == "approved"
    assert result["status"] == "compliance_approved"


def test_reporting_threshold_flag(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "passed_fraud"
    base_txn["amount"] = "10000.00"
    result = cc.check_compliance(base_txn)
    assert "regulatory_report_required" in result["compliance_flags"]


def test_below_threshold_no_flag(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "passed_fraud"
    base_txn["amount"] = "9999.99"
    result = cc.check_compliance(base_txn)
    assert "regulatory_report_required" not in result["compliance_flags"]


def test_blocked_account_rejected(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "passed_fraud"
    base_txn["destination_account"] = "ACC-9999"
    result = cc.check_compliance(base_txn)
    assert result["status"] == "rejected"
    assert result["reason"] == "blocked_account"


def test_fraud_review_held(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "fraud_review"
    result = cc.check_compliance(base_txn)
    assert result["status"] == "held"
    assert result["reason"] == "fraud_review"


def test_process_message_targets_settlement(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "passed_fraud"
    msg = Message("fraud_detector", "compliance_checker", "transaction", base_txn)
    out = cc.process_message(msg.to_dict())
    assert out["target_agent"] == "settlement_processor"
