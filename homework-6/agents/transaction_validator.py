"""Agent 1 of the pipeline: the Transaction Validator.

Checks that each raw transaction has the required fields, a well-formed
monetary amount and a supported ISO 4217 currency. Valid transactions are
marked ``validated``; anything else is ``rejected`` with a human-readable
reason. The agent never logs account numbers or descriptions in plaintext.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from agents.common import (
    SUPPORTED_CURRENCIES,
    AgentError,
    Message,
    audit,
    configure_audit_logger,
    mask_account,
    parse_money,
    quantize_money,
)

AGENT_NAME = "transaction_validator"
REQUIRED_FIELDS = (
    "transaction_id",
    "timestamp",
    "source_account",
    "destination_account",
    "amount",
    "currency",
    "transaction_type",
)


def _missing_fields(record: dict[str, Any]) -> list[str]:
    """Return reasons for any required fields that are missing/empty."""

    return [f"missing required field: {name}" for name in REQUIRED_FIELDS if not record.get(name)]


def _amount_reasons(amount: Decimal, is_refund: bool) -> list[str]:
    """Return reasons why ``amount`` is invalid for the given transaction kind."""

    if amount == 0:
        return ["amount must be non-zero"]
    if amount < 0 and not is_refund:
        return ["negative amount only allowed for refunds"]
    return []


def _value_reasons(record: dict[str, Any], currency: str) -> tuple[list[str], Decimal | None]:
    """Validate currency and amount; return (reasons, parsed-amount-or-None)."""

    reasons: list[str] = []
    if currency not in SUPPORTED_CURRENCIES:
        reasons.append(f"unsupported currency: {currency}")

    try:
        amount = parse_money(record["amount"])
    except AgentError as exc:
        return reasons + [str(exc)], None

    is_refund = str(record.get("transaction_type")) == "refund"
    reasons += _amount_reasons(amount, is_refund)
    return reasons, amount


def validate_transaction(record: dict[str, Any]) -> dict[str, Any]:
    """Validate one raw transaction record.

    Returns a dict with at least ``status`` (``"validated"`` / ``"rejected"``)
    and, when rejected, a ``reason``. On success the ``amount`` is normalised
    to its currency's minor units (as a string) so downstream agents inherit a
    canonical value.
    """

    missing = _missing_fields(record)
    if missing:
        return {**record, "status": "rejected", "reason": "; ".join(missing)}

    currency = str(record["currency"]).upper()
    reasons, amount = _value_reasons(record, currency)
    if reasons or amount is None:
        return {**record, "status": "rejected", "reason": "; ".join(reasons)}

    normalised = quantize_money(amount, currency)
    return {
        **record,
        "currency": currency,
        "amount": str(normalised),
        "status": "validated",
    }


def process_message(message: dict[str, Any]) -> dict[str, Any]:
    """Process an inbound envelope and return the outbound envelope dict.

    This is the uniform agent entry point referenced by the specification's
    Low-Level Tasks: ``process_message(message: dict) -> dict``.
    """

    inbound = Message.from_dict(message)
    result = validate_transaction(inbound.data)
    target = "fraud_detector" if result["status"] == "validated" else "reporting_agent"
    outbound = Message(
        source_agent=AGENT_NAME,
        target_agent=target,
        message_type="transaction",
        data=result,
    )
    return outbound.to_dict()


def run(
    paths_input: Path,
    paths_output: Path,
    logger: logging.Logger,
) -> list[Path]:
    """Validate every message in ``paths_input``; write results to ``paths_output``."""

    written: list[Path] = []
    for message_file in sorted(paths_input.glob("*.json")):
        inbound = json.loads(message_file.read_text(encoding="utf-8"))
        outbound = process_message(inbound)
        data = outbound["data"]
        path = Message.from_dict(outbound).write(paths_output)
        audit(
            logger,
            AGENT_NAME,
            data.get("transaction_id", "?"),
            data["status"],
            detail=f"src={mask_account(str(data.get('source_account', '')))}",
        )
        written.append(path)
    return written


def _dry_run(sample_path: Path) -> int:
    """Validate a sample file without producing pipeline output (``--dry-run``)."""

    records = json.loads(sample_path.read_text(encoding="utf-8"))
    valid, invalid = 0, 0
    rows: list[str] = []
    for record in records:
        result = validate_transaction(record)
        status = result["status"]
        if status == "validated":
            valid += 1
        else:
            invalid += 1
        reason = result.get("reason", "-")
        rows.append(f"{record.get('transaction_id', '?'):<8} {status:<10} {reason}")

    print(f"Total: {len(records)}  Valid: {valid}  Invalid: {invalid}")
    print(f"{'TXN':<8} {'STATUS':<10} REASON")
    print("\n".join(rows))
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. ``--dry-run`` validates the sample file only."""

    parser = argparse.ArgumentParser(description="Transaction validator agent")
    parser.add_argument("--dry-run", action="store_true", help="validate sample only")
    parser.add_argument(
        "--sample",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "sample-transactions.json",
    )
    args = parser.parse_args(argv)

    configure_audit_logger()
    if args.dry_run:
        return _dry_run(args.sample)
    print("Run the full pipeline with: python integrator.py")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI shim
    sys.exit(main())
