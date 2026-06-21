"""Core transaction logic for paycli.

NOTE: this module contains intentional seeded bugs for the pipeline to find and fix
(see context/bugs/001/bug-context.md). Do not "pre-fix" them by hand.
"""

from __future__ import annotations

from collections.abc import Sequence


def total(amounts: Sequence[float]) -> float:
    """Return the sum of transaction amounts."""
    return sum(amounts)


def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount.

    BUG-B: divides by ``len`` with no guard for an empty sequence, so an empty
    input raises ``ZeroDivisionError`` instead of returning 0.
    """
    return sum(amounts) / len(amounts)


def is_within_daily_limit(spent: float, amount: float, limit: float) -> bool:
    """Return True if charging ``amount`` keeps the day's total within ``limit``.

    BUG-A: uses a strict ``<`` comparison, so a spend that lands *exactly* on the
    limit is wrongly rejected (off-by-one boundary error). Should be ``<=``.
    """
    return spent + amount < limit
