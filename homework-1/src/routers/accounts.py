"""/accounts routes: balance (Task 1), summary (4-A), interest (4-B)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src import services
from src.deps import get_store
from src.store import TransactionStore

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/{account_id}/balance")
def get_balance(
    account_id: str,
    store: TransactionStore = Depends(get_store),
) -> dict:
    balance = services.compute_balance(store.list(), account_id)
    return {"accountId": account_id, "balance": float(balance)}


@router.get("/{account_id}/summary")
def get_summary(
    account_id: str,
    store: TransactionStore = Depends(get_store),
) -> dict:
    return services.account_summary(store.list(), account_id)


@router.get("/{account_id}/interest")
def get_interest(
    account_id: str,
    rate: float = Query(..., description="Annual interest rate, e.g. 0.05"),
    days: int = Query(..., description="Number of days"),
    store: TransactionStore = Depends(get_store),
) -> dict:
    balance = services.compute_balance(store.list(), account_id)
    interest = services.simple_interest(balance, rate, days)
    return {
        "accountId": account_id,
        "balance": float(balance),
        "rate": rate,
        "days": days,
        "interest": float(interest),
    }
