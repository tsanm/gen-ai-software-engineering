"""Agent 4 of the pipeline: the Settlement Processor.

Produces the final outcome for each transaction. Only compliance-approved
transactions settle; held or rejected ones are passed through unchanged with
their existing status. Settlement computes a fee and the net amount using
``Decimal`` arithmetic with ``ROUND_HALF_UP`` quantisation so the books always
balance to the currency's minor unit.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from agents.common import Message, load_config, parse_money, quantize_money

AGENT_NAME = "settlement_processor"

#: Flat proportional settlement fee (0.25%), sourced from ``pipeline.config.json``.
FEE_RATE = Decimal(str(load_config()["settlement"]["fee_rate"]))


def settle(record: dict[str, Any]) -> dict[str, Any]:
    """Return ``record`` with a terminal settlement outcome.

    Approved transactions get ``fee``, ``net_amount`` and ``status=settled``.
    Held/rejected transactions keep their inbound status and gain no fees.
    """

    if record.get("status") != "compliance_approved":
        # Held or rejected: terminal but not settled.
        final_status = record.get("status", "rejected")
        return {**record, "settlement_status": final_status, "status": final_status}

    currency = str(record["currency"])
    amount = parse_money(record["amount"])
    fee = quantize_money(abs(amount) * FEE_RATE, currency)
    net = quantize_money(amount - fee if amount > 0 else amount + fee, currency)

    return {
        **record,
        "fee": str(fee),
        "net_amount": str(net),
        "settlement_status": "settled",
        "status": "settled",
    }


def process_message(message: dict[str, Any]) -> dict[str, Any]:
    """Settle the inbound transaction and forward the final record to reporting."""

    inbound = Message.from_dict(message)
    settled = settle(inbound.data)
    outbound = Message(
        source_agent=AGENT_NAME,
        target_agent="reporting_agent",
        message_type="transaction",
        data=settled,
    )
    return outbound.to_dict()
