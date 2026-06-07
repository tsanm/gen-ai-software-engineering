"""/transactions routes (Tasks 1, 3, and 4-C)."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query, Response

from src import currencies, services
from src.compliance import AuditLog, CompliancePolicy, mask_account
from src.deps import get_audit, get_policy, get_region, get_request_id, get_store
from src.errors import ApiError, ValidationProblem
from src.models import Status, Transaction, TransactionCreate, TxType
from src.regions import Region
from src.store import TransactionStore
from src.validators import validate_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", status_code=201)
def create_transaction(
    payload: TransactionCreate,
    store: TransactionStore = Depends(get_store),
    region: Region = Depends(get_region),
    audit: AuditLog = Depends(get_audit),
    policy: CompliancePolicy = Depends(get_policy),
    request_id: str | None = Depends(get_request_id),
) -> Transaction:
    details = validate_transaction(payload, region)
    if details:
        raise ValidationProblem(details)

    txn = Transaction(
        id=str(uuid.uuid4()),
        fromAccount=payload.fromAccount,
        toAccount=payload.toAccount,
        amount=currencies.quantize(payload.currency, payload.amount),
        currency=payload.currency.upper(),
        type=payload.type,
        timestamp=datetime.now(timezone.utc),
        status=Status.completed,
    )
    store.add(txn)

    # Compliance review + audit trail (PII masked).
    flags = policy.review(txn.amount)
    meta = {
        "type": txn.type.value,
        "currency": txn.currency,
        "fromAccount": mask_account(txn.fromAccount),
        "toAccount": mask_account(txn.toAccount),
    }
    audit.record("transaction.created", txn.id, request_id, meta)
    if flags:
        audit.record("compliance.flagged", txn.id, request_id, {**meta, "flags": flags})

    return txn


@router.get("")
def list_transactions(
    store: TransactionStore = Depends(get_store),
    accountId: str | None = Query(None),
    type: TxType | None = Query(None),
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
) -> list[Transaction]:
    return services.filter_transactions(
        store.list(), account_id=accountId, tx_type=type,
        date_from=date_from, date_to=date_to)


# Declared BEFORE /{transaction_id} so "export" is not captured as an id.
@router.get("/export")
def export_transactions(
    format: str = Query("csv"),
    store: TransactionStore = Depends(get_store),
) -> Response:
    if format != "csv":
        raise ApiError(400, "Unsupported export format", [
            {"field": "format", "message": "Only 'csv' is supported"}])
    csv_text = services.transactions_to_csv(store.list())
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"})


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: str,
    store: TransactionStore = Depends(get_store),
) -> Transaction:
    txn = store.get(transaction_id)
    if txn is None:
        raise ApiError(404, "Transaction not found")
    return txn
