"""Input validation for account-scoped queries (balance / summary / interest).

Previously these endpoints accepted any path/query value unchecked. For a banking API,
validating the account identifier and numeric parameters is mandatory -- a malformed
account id or a negative rate/term is a client error (400), not a silent zero result.
Each helper raises `ValidationProblem`, which renders as the shared 400 envelope.
"""
from __future__ import annotations

import math

from src.errors import ValidationProblem
from src.services.regions import Region
from src.validators.transaction_validator import ACCOUNT_FORMAT_MSG


def validate_account_id(account_id: str, region: Region) -> None:
    """Reject an account id that does not match the region's account format."""
    if not region.is_valid_account(account_id):
        raise ValidationProblem([{"field": "accountId", "message": ACCOUNT_FORMAT_MSG}])


def validate_interest_params(rate: float, days: int) -> None:
    """Reject invalid interest inputs (type coercion is handled upstream by FastAPI).

    A non-finite rate (e.g. ``rate=1e400`` coerced to ``inf``) is rejected explicitly --
    otherwise it would propagate as a non-JSON-serializable ``Infinity`` and surface as a
    500 instead of a clean 400.
    """
    details: list[dict] = []
    if not math.isfinite(rate):
        details.append({"field": "rate", "message": "Rate must be a finite number"})
    elif rate < 0:
        details.append({"field": "rate", "message": "Rate must be zero or positive"})
    if days < 0:
        details.append({"field": "days", "message": "Days must be zero or positive"})
    if details:
        raise ValidationProblem(details)
