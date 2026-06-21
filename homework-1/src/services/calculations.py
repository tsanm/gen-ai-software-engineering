"""Pure domain calculations: filtering, balance, summary, interest, CSV export.

Pure functions over lists of `Transaction` -- no framework, storage, or transport
coupling, which keeps them trivially testable and reusable by the application services.
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal

from src.models import Status, Transaction, TxType


def _involves(txn: Transaction, account_id: str) -> bool:
    return account_id in (txn.fromAccount, txn.toAccount)


def filter_transactions(
    txns: list[Transaction],
    account_id: str | None = None,
    tx_type: TxType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Transaction]:
    """Apply Task 3 filters with AND semantics. accountId matches sender OR receiver."""
    predicates = []
    if account_id:
        predicates.append(lambda t: _involves(t, account_id))
    if tx_type:
        predicates.append(lambda t: t.type == tx_type)
    if date_from:
        predicates.append(lambda t: t.timestamp.date() >= date_from)
    if date_to:
        predicates.append(lambda t: t.timestamp.date() <= date_to)
    return [t for t in txns if all(p(t) for p in predicates)]


def compute_balance(txns: list[Transaction], account_id: str) -> Decimal:
    """Net balance from completed transactions only."""
    balance = Decimal("0")
    for t in txns:
        if t.status != Status.completed:
            continue
        if t.type == TxType.deposit and t.toAccount == account_id:
            balance += t.amount
        elif t.type == TxType.withdrawal and t.fromAccount == account_id:
            balance -= t.amount
        elif t.type == TxType.transfer:
            if t.fromAccount == account_id:
                balance -= t.amount
            if t.toAccount == account_id:
                balance += t.amount
    return balance


def _is_deposit_to(account_id: str):
    return lambda t: t.type == TxType.deposit and t.toAccount == account_id


def _is_withdrawal_from(account_id: str):
    return lambda t: t.type == TxType.withdrawal and t.fromAccount == account_id


def _sum_amounts(txns, predicate) -> Decimal:
    return sum((t.amount for t in txns if predicate(t)), Decimal("0"))


def account_summary(txns: list[Transaction], account_id: str) -> dict:
    """Task 4-A: totals, count, and most-recent date for an account.

    Returns raw domain values (Decimal totals, `datetime`); JSON shaping is the view
    model's job, not the domain's.
    """
    involved = [t for t in txns if _involves(t, account_id)]
    total_deposits = _sum_amounts(involved, _is_deposit_to(account_id))
    total_withdrawals = _sum_amounts(involved, _is_withdrawal_from(account_id))
    most_recent: datetime | None = max((t.timestamp for t in involved), default=None)
    return {
        "accountId": account_id,
        "totalDeposits": total_deposits,
        "totalWithdrawals": total_withdrawals,
        "transactionCount": len(involved),
        "mostRecentTransactionDate": most_recent,
    }


def simple_interest(balance: Decimal, rate: float, days: int) -> Decimal:
    """Task 4-B: simple interest = balance * rate * (days / 365)."""
    return balance * Decimal(str(rate)) * Decimal(days) / Decimal(365)


def transactions_to_csv(txns: list[Transaction]) -> str:
    """Task 4-C: serialize transactions to CSV."""
    buffer = io.StringIO()
    fields = ["id", "fromAccount", "toAccount", "amount", "currency",
              "type", "timestamp", "status"]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for t in txns:
        writer.writerow({
            "id": t.id,
            "fromAccount": t.fromAccount or "",
            "toAccount": t.toAccount or "",
            "amount": f"{t.amount}",
            "currency": t.currency,
            "type": t.type.value,
            "timestamp": t.timestamp.isoformat(),
            "status": t.status.value,
        })
    return buffer.getvalue()
