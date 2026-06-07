"""Domain models and API schemas (Pydantic v2)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, field_serializer, field_validator


class TxType(str, Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    transfer = "transfer"


class Status(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class TransactionCreate(BaseModel):
    """Incoming POST body. Domain rules (amount/account/currency) are enforced in
    `validators.validate_transaction`; Pydantic only guarantees basic types here."""

    fromAccount: str | None = None
    toAccount: str | None = None
    amount: Decimal
    currency: str
    type: TxType

    @field_validator("fromAccount", "toAccount", mode="before")
    @classmethod
    def _blank_to_none(cls, value):
        """Treat blank/whitespace-only account strings as absent (None)."""
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


class Transaction(BaseModel):
    """Stored + returned transaction."""

    id: str
    fromAccount: str | None
    toAccount: str | None
    amount: Decimal
    currency: str
    type: TxType
    timestamp: datetime
    status: Status

    @field_serializer("amount")
    def _serialize_amount(self, value: Decimal) -> float:
        # Spec models `amount` as a JSON number; internal math stays Decimal.
        return float(value)
