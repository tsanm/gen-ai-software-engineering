"""Compliance: audit trail and a pluggable policy hook (a business concern).

Deliberately lightweight (in-memory) but models the seams a real bank needs: an immutable
audit log and a per-region policy that can flag transactions (e.g. AML/CTR large-amount
reporting). PII redaction itself is a generic helper -- see `utils.masking`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


class AuditLog:
    """Append-only, in-memory audit trail. One instance per app (see app.state)."""

    def __init__(self) -> None:
        self.entries: list[dict] = []

    def record(self, action: str, entity_id: str, request_id: str | None,
               metadata: dict | None = None) -> None:
        self.entries.append({
            "action": action,
            "entityId": entity_id,
            "requestId": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        })


@dataclass(frozen=True)
class CompliancePolicy:
    """Region-configurable policy. Default rule: flag large transactions for reporting."""

    large_amount_threshold: Decimal = field(default=Decimal("10000"))

    def review(self, amount: Decimal) -> list[str]:
        flags: list[str] = []
        if amount >= self.large_amount_threshold:
            flags.append("large_transaction")
        return flags
