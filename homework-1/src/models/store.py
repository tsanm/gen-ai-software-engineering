"""In-memory transaction store (data-access layer).

Encapsulated behind a tiny interface so the persistence mechanism can be swapped for a
real database later without touching routes or services. One instance per app (app.state).
"""
from __future__ import annotations

from src.models.transaction import Transaction


class TransactionStore:
    def __init__(self) -> None:
        self._by_id: dict[str, Transaction] = {}

    def add(self, txn: Transaction) -> Transaction:
        self._by_id[txn.id] = txn
        return txn

    def get(self, txn_id: str) -> Transaction | None:
        return self._by_id.get(txn_id)

    def list(self) -> list[Transaction]:
        return list(self._by_id.values())
