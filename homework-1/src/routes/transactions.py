"""/transactions routes (Tasks 1, 3, and 4-C).

Thin adapters over `TransactionService`; all domain logic, validation, compliance, and
audit live in the service.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Response

from src.errors import ApiError
from src.models import Transaction, TransactionCreate, TxType
from src.routes.dependencies import get_transaction_service
from src.services import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", status_code=201)
def create_transaction(
    payload: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
) -> Transaction:
    return service.create(payload)


@router.get("")
def list_transactions(
    service: TransactionService = Depends(get_transaction_service),
    accountId: str | None = Query(None),
    type: TxType | None = Query(None),
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
) -> list[Transaction]:
    return service.list(
        account_id=accountId, tx_type=type, date_from=date_from, date_to=date_to)


# Declared BEFORE /{transaction_id} so "export" is not captured as an id.
@router.get("/export")
def export_transactions(
    format: str = Query("csv"),
    service: TransactionService = Depends(get_transaction_service),
) -> Response:
    if format != "csv":
        raise ApiError(400, "Unsupported export format", [
            {"field": "format", "message": "Only 'csv' is supported"}])
    csv_text = service.export_csv()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"})


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> Transaction:
    return service.get(transaction_id)
