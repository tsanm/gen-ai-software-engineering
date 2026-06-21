"""Agent 3 of the pipeline: the Compliance Checker.

Applies regulatory rules on top of the fraud score:

* transactions flagged ``fraud_review`` are held (never auto-settled),
* large transactions trigger a simulated regulatory report threshold
  (e.g. a Currency Transaction Report style threshold at 10,000),
* transactions to/from blocked accounts are rejected outright.

The decision and any required filings are attached to the record for the
settlement processor and the audit trail.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from agents.common import Message, parse_money

AGENT_NAME = "compliance_checker"

#: Amount (major units) at/above which a regulatory report flag is raised.
REPORTING_THRESHOLD = Decimal("10000")

#: Demo blocklist of sanctioned/frozen account identifiers.
BLOCKED_ACCOUNTS = frozenset({"ACC-9999"})


def check_compliance(record: dict[str, Any]) -> dict[str, Any]:
    """Return ``record`` with a compliance decision and any report flags."""

    flags: list[str] = []
    amount = parse_money(record["amount"])

    if abs(amount) >= REPORTING_THRESHOLD:
        flags.append("regulatory_report_required")

    blocked = {
        str(record.get("source_account")),
        str(record.get("destination_account")),
    } & BLOCKED_ACCOUNTS

    if blocked:
        decision = "rejected"
        status = "rejected"
        reason = "blocked_account"
    elif record.get("status") == "fraud_review":
        decision = "held"
        status = "held"
        reason = "fraud_review"
    else:
        decision = "approved"
        status = "compliance_approved"
        reason = ""

    result = {
        **record,
        "compliance_decision": decision,
        "compliance_flags": flags,
        "status": status,
    }
    if reason:
        result["reason"] = reason
    return result


def process_message(message: dict[str, Any]) -> dict[str, Any]:
    """Screen the inbound transaction and forward it to settlement."""

    inbound = Message.from_dict(message)
    checked = check_compliance(inbound.data)
    outbound = Message(
        source_agent=AGENT_NAME,
        target_agent="settlement_processor",
        message_type="transaction",
        data=checked,
    )
    return outbound.to_dict()
