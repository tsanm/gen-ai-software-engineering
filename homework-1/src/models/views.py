"""Outbound view models (read DTOs) returned by the application services.

Keeping these here -- rather than assembling ad-hoc dicts in a route handler -- means the
*same* transport-agnostic object is produced by a use-case no matter what triggers it
(HTTP route today; an SQS consumer, gRPC service, or CLI tomorrow). Money is carried as
`Decimal` internally and serialized to a JSON number only at the edge.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class BalanceView(BaseModel):
    """Result of an account-balance query (Task 1)."""

    accountId: str
    balance: Decimal

    @field_serializer("balance")
    def _money(self, value: Decimal) -> float:
        return float(value)


class AccountSummaryView(BaseModel):
    """Result of an account-summary query (Task 4-A)."""

    accountId: str
    totalDeposits: Decimal
    totalWithdrawals: Decimal
    transactionCount: int
    mostRecentTransactionDate: datetime | None

    @field_serializer("totalDeposits", "totalWithdrawals")
    def _money(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("mostRecentTransactionDate")
    def _timestamp(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None


class InterestView(BaseModel):
    """Result of a simple-interest calculation (Task 4-B)."""

    accountId: str
    balance: Decimal
    rate: float
    days: int
    interest: Decimal

    @field_serializer("balance", "interest")
    def _money(self, value: Decimal) -> float:
        return float(value)
