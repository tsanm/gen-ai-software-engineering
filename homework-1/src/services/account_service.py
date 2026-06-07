"""Application service for account queries (Tasks 1, 4-A, 4-B).

This is the business layer. It owns input validation and *builds the response view
models* so the transport layer (HTTP route, queue consumer, CLI) only adapts, never
shapes, the result. The same `AccountService` could be driven from an SQS handler and
return the identical `BalanceView` / `AccountSummaryView` / `InterestView`.
"""
from __future__ import annotations

from src.models import AccountSummaryView, BalanceView, InterestView
from src.models.store import TransactionStore
from src.services import calculations
from src.services.regions import Region
from src.validators import validate_account_id, validate_interest_params


class AccountService:
    def __init__(self, store: TransactionStore, region: Region) -> None:
        self._store = store
        self._region = region

    def get_balance(self, account_id: str) -> BalanceView:
        validate_account_id(account_id, self._region)
        balance = calculations.compute_balance(self._store.list(), account_id)
        return BalanceView(accountId=account_id, balance=balance)

    def get_summary(self, account_id: str) -> AccountSummaryView:
        validate_account_id(account_id, self._region)
        return AccountSummaryView(**calculations.account_summary(self._store.list(), account_id))

    def get_interest(self, account_id: str, rate: float, days: int) -> InterestView:
        validate_account_id(account_id, self._region)
        validate_interest_params(rate, days)
        balance = calculations.compute_balance(self._store.list(), account_id)
        interest = calculations.simple_interest(balance, rate, days)
        return InterestView(
            accountId=account_id, balance=balance, rate=rate, days=days, interest=interest)
