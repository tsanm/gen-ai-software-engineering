"""/accounts routes: balance (Task 1), summary (4-A), interest (4-B).

Thin adapters over `AccountService`. Input validation and response shaping live in the
service / view models, not here.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.models import AccountSummaryView, BalanceView, InterestView
from src.routes.dependencies import get_account_service
from src.services import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/{account_id}/balance")
def get_balance(
    account_id: str,
    service: AccountService = Depends(get_account_service),
) -> BalanceView:
    return service.get_balance(account_id)


@router.get("/{account_id}/summary")
def get_summary(
    account_id: str,
    service: AccountService = Depends(get_account_service),
) -> AccountSummaryView:
    return service.get_summary(account_id)


@router.get("/{account_id}/interest")
def get_interest(
    account_id: str,
    rate: float = Query(..., description="Annual interest rate, e.g. 0.05"),
    days: int = Query(..., description="Number of days"),
    service: AccountService = Depends(get_account_service),
) -> InterestView:
    return service.get_interest(account_id, rate, days)
