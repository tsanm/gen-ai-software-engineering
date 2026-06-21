"""Unit tests for the transaction validator agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents import transaction_validator as tv
from agents.common import Message


def test_valid_transaction_passes(base_txn: dict[str, Any]) -> None:
    result = tv.validate_transaction(base_txn)
    assert result["status"] == "validated"
    assert result["amount"] == "100.00"


def test_missing_field_rejected(base_txn: dict[str, Any]) -> None:
    del base_txn["amount"]
    result = tv.validate_transaction(base_txn)
    assert result["status"] == "rejected"
    assert "amount" in result["reason"]


def test_unsupported_currency_rejected(base_txn: dict[str, Any]) -> None:
    base_txn["currency"] = "XYZ"
    result = tv.validate_transaction(base_txn)
    assert result["status"] == "rejected"
    assert "currency" in result["reason"]


def test_zero_amount_rejected(base_txn: dict[str, Any]) -> None:
    base_txn["amount"] = "0.00"
    result = tv.validate_transaction(base_txn)
    assert result["status"] == "rejected"
    assert "non-zero" in result["reason"]


def test_negative_amount_rejected_for_transfer(base_txn: dict[str, Any]) -> None:
    base_txn["amount"] = "-50.00"
    result = tv.validate_transaction(base_txn)
    assert result["status"] == "rejected"


def test_negative_amount_allowed_for_refund(base_txn: dict[str, Any]) -> None:
    base_txn["amount"] = "-50.00"
    base_txn["transaction_type"] = "refund"
    result = tv.validate_transaction(base_txn)
    assert result["status"] == "validated"


def test_currency_normalised_uppercase(base_txn: dict[str, Any]) -> None:
    base_txn["currency"] = "usd"
    result = tv.validate_transaction(base_txn)
    assert result["currency"] == "USD"


def test_amount_invalid_string_rejected(base_txn: dict[str, Any]) -> None:
    base_txn["amount"] = "abc"
    result = tv.validate_transaction(base_txn)
    assert result["status"] == "rejected"


def test_process_message_routes_valid(base_txn: dict[str, Any]) -> None:
    msg = Message("integrator", "transaction_validator", "transaction", base_txn)
    out = tv.process_message(msg.to_dict())
    assert out["target_agent"] == "fraud_detector"
    assert out["data"]["status"] == "validated"


def test_process_message_routes_rejected(base_txn: dict[str, Any]) -> None:
    base_txn["currency"] = "XYZ"
    msg = Message("integrator", "transaction_validator", "transaction", base_txn)
    out = tv.process_message(msg.to_dict())
    assert out["target_agent"] == "reporting_agent"


def test_run_writes_outputs(base_txn: dict[str, Any], tmp_path: Path) -> None:
    from agents.common import PipelinePaths, configure_audit_logger

    paths = PipelinePaths.create(tmp_path / "shared")
    Message("integrator", "transaction_validator", "transaction", base_txn).write(paths.input)
    logger = configure_audit_logger(tmp_path / "audit.log")
    written = tv.run(paths.input, paths.output, logger)
    assert len(written) == 1
    assert written[0].exists()


def test_dry_run_cli(sample_path: Path, capsys: Any) -> None:
    rc = tv.main(["--dry-run", "--sample", str(sample_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total: 3" in out
    assert "Valid:" in out


def test_main_without_dry_run(capsys: Any) -> None:
    rc = tv.main([])
    assert rc == 0
    assert "integrator.py" in capsys.readouterr().out
