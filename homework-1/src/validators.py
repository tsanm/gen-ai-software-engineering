"""Domain validation for transactions (Task 2).

Produces the documented error-detail list. All rules are checked so the response can
report every problem at once, matching the spec's multi-error example.
"""
from __future__ import annotations

from decimal import Decimal

from src import currencies
from src.models import TransactionCreate, TxType
from src.regions import Region

ACCOUNT_FORMAT_MSG = "Account must match format ACC-XXXXX (5 alphanumeric characters)"


def _detail(field: str, message: str) -> dict:
    return {"field": field, "message": message}


def validate_transaction(payload: TransactionCreate, region: Region) -> list[dict]:
    details: list[dict] = []

    # --- amount ---
    amount: Decimal = payload.amount
    if amount is None or amount <= 0:
        details.append(_detail("amount", "Amount must be a positive number"))

    # --- currency (validate before precision, which depends on it) ---
    currency_ok = currencies.is_valid_currency(payload.currency)
    if not currency_ok:
        details.append(_detail("currency", "Invalid currency code"))
    elif (region.allowed_currencies
          and payload.currency.upper() not in region.allowed_currencies):
        details.append(_detail(
            "currency",
            f"Currency {payload.currency} is not supported in region {region.code}"))

    # --- amount precision (currency-aware) ---
    if amount is not None and amount > 0 and currency_ok:
        if not currencies.has_valid_precision(payload.currency, amount):
            allowed = currencies.minor_units(payload.currency)
            details.append(_detail(
                "amount",
                f"Amount exceeds the maximum {allowed} decimal place(s) for {payload.currency}"))

    # --- per-type account rules ---
    details.extend(_validate_accounts(payload, region))

    return details


def _validate_accounts(payload: TransactionCreate, region: Region) -> list[dict]:
    details: list[dict] = []
    frm, to = payload.fromAccount, payload.toAccount

    def check_format(field: str, value: str | None) -> None:
        if value is not None and not region.is_valid_account(value):
            details.append(_detail(field, ACCOUNT_FORMAT_MSG))

    if payload.type == TxType.deposit:
        if not to:
            details.append(_detail("toAccount", "Deposit requires a destination account"))
        if frm:
            details.append(_detail("fromAccount", "Deposit must not specify a source account"))
        check_format("toAccount", to)

    elif payload.type == TxType.withdrawal:
        if not frm:
            details.append(_detail("fromAccount", "Withdrawal requires a source account"))
        if to:
            details.append(_detail(
                "toAccount", "Withdrawal must not specify a destination account"))
        check_format("fromAccount", frm)

    elif payload.type == TxType.transfer:
        if not frm:
            details.append(_detail("fromAccount", "Transfer requires a source account"))
        if not to:
            details.append(_detail("toAccount", "Transfer requires a destination account"))
        if frm and to and frm == to:
            details.append(_detail("toAccount", "Transfer source and destination must differ"))
        check_format("fromAccount", frm)
        check_format("toAccount", to)

    return details
