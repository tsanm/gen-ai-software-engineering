"""Unit tests for the settlement processor agent."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from agents import settlement_processor as sp
from agents.common import Message, parse_money


def test_settles_approved(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "compliance_approved"
    base_txn["amount"] = "1000.00"
    result = sp.settle(base_txn)
    assert result["status"] == "settled"
    # fee = 1000 * 0.0025 = 2.50; net = 997.50
    assert result["fee"] == "2.50"
    assert result["net_amount"] == "997.50"


def test_fee_rounds_half_up(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "compliance_approved"
    base_txn["amount"] = "100.10"  # fee = 0.25025 -> 0.25
    result = sp.settle(base_txn)
    assert parse_money(result["fee"]) == Decimal("0.25")


def test_refund_negative_net(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "compliance_approved"
    base_txn["amount"] = "-100.00"
    base_txn["transaction_type"] = "refund"
    result = sp.settle(base_txn)
    # net = amount + fee (fee added back toward zero on a negative amount)
    assert parse_money(result["net_amount"]) == Decimal("-99.75")


def test_held_not_settled(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "held"
    result = sp.settle(base_txn)
    assert result["status"] == "held"
    assert "fee" not in result


def test_rejected_passthrough(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "rejected"
    result = sp.settle(base_txn)
    assert result["status"] == "rejected"


def test_process_message_targets_reporting(base_txn: dict[str, Any]) -> None:
    base_txn["status"] = "compliance_approved"
    msg = Message("compliance_checker", "settlement_processor", "transaction", base_txn)
    out = sp.process_message(msg.to_dict())
    assert out["target_agent"] == "reporting_agent"
