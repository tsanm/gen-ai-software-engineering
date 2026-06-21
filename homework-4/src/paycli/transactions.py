"""Core transaction logic for paycli."""

from __future__ import annotations

from collections.abc import Sequence


def total(amounts: Sequence[float]) -> float:
    """Return the sum of transaction amounts."""
    return sum(amounts)


def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount; 0.0 for an empty sequence."""
    if not amounts:
        return 0.0
    return sum(amounts) / len(amounts)


def is_within_daily_limit(spent: float, amount: float, limit: float) -> bool:
    """Return True if charging ``amount`` keeps the day's total within ``limit``.

    A spend that lands exactly on ``limit`` is allowed (inclusive upper bound).
    """
    return spent + amount <= limit
