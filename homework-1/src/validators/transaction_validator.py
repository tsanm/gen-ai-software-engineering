"""Domain validation for transactions (Task 2).

Produces the documented error-detail list. All rules are checked so the response can
report every problem at once, matching the spec's multi-error example.
"""
from __future__ import annotations

from decimal import Decimal

from src.models import TransactionCreate, TxType
from src.services import currencies
from src.services.regions import Region

ACCOUNT_FORMAT_MSG = "Account must match format ACC-XXXXX (5 alphanumeric characters)"

# Upper bound on a single transaction amount. Besides being a sane banking control, this
# keeps values well within the Decimal context precision so `currencies.quantize` can
# never raise InvalidOperation on an absurd magnitude (which would surface as a 500).
MAX_AMOUNT = Decimal("1_000_000_000_000")  # 1 trillion


def _detail(field: str, message: str) -> dict:
    return {"field": field, "message": message}


def validate_transaction(payload: TransactionCreate, region: Region) -> list[dict]:
    details: list[dict] = []

    # --- amount ---
    # NaN/Infinity are rejected upstream by Pydantic, so `amount` is always finite here.
    amount: Decimal = payload.amount
    if amount is None or amount <= 0:
        details.append(_detail("amount", "Amount must be a positive number"))
    elif amount > MAX_AMOUNT:
        details.append(_detail("amount", f"Amount exceeds the maximum allowed value of {MAX_AMOUNT}"))

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
    """Validate the account fields per transaction type.

    Rules: each type must carry its *essential* account, a transfer's two accounts must
    differ, and any account that IS provided must match the region format. Presence of an
    extra account is allowed (the spec models both fields as strings for every type).
    """
    frm, to = payload.fromAccount, payload.toAccount
    details = _required_account_errors(payload.type, frm, to)

    # Format is validated for whichever accounts are present, regardless of type.
    for field, value in (("fromAccount", frm), ("toAccount", to)):
        if value is not None and not region.is_valid_account(value):
            details.append(_detail(field, ACCOUNT_FORMAT_MSG))

    return details


def _required_account_errors(tx_type: TxType, frm: str | None, to: str | None) -> list[dict]:
    """Per-type presence rules for the essential account(s)."""
    if tx_type == TxType.deposit:
        return [] if to else [_detail("toAccount", "Deposit requires a destination account")]
    if tx_type == TxType.withdrawal:
        return [] if frm else [_detail("fromAccount", "Withdrawal requires a source account")]

    # transfer: both required and distinct
    errors: list[dict] = []
    if not frm:
        errors.append(_detail("fromAccount", "Transfer requires a source account"))
    if not to:
        errors.append(_detail("toAccount", "Transfer requires a destination account"))
    if frm and to and frm == to:
        errors.append(_detail("toAccount", "Transfer source and destination must differ"))
    return errors
