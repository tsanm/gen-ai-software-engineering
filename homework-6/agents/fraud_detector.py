"""Agent 2 of the pipeline: the Fraud Detector.

Scores each validated transaction for risk and assigns a band. The score is a
weighted sum of independent heuristics so the rationale is fully explainable:

* high-value amounts (graduated thresholds),
* off-hours activity (00:00-05:00 local-to-UTC window),
* cross-border transactions (source country != destination heuristic),
* wire transfers (a higher-risk rail).

Transactions scoring at or above the review threshold are flagged for manual
fraud review; everything else passes straight through to compliance.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from agents.common import Message, parse_money

AGENT_NAME = "fraud_detector"

#: Score at/above which a transaction is flagged for manual fraud review.
REVIEW_THRESHOLD = 50

#: Graduated high-value thresholds (amount in major units) -> points.
HIGH_VALUE_BANDS: tuple[tuple[Decimal, int], ...] = (
    (Decimal("50000"), 50),
    (Decimal("10000"), 30),
    (Decimal("5000"), 15),
)


def _high_value_points(amount: Decimal) -> tuple[int, str | None]:
    magnitude = abs(amount)
    for threshold, points in HIGH_VALUE_BANDS:
        if magnitude >= threshold:
            return points, f"high_value>={threshold}"
    return 0, None


def _off_hours_points(timestamp: str) -> tuple[int, str | None]:
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return 0, None
    if 0 <= parsed.hour < 5:
        return 20, "off_hours"
    return 0, None


def _cross_border_points(record: dict[str, Any]) -> tuple[int, str | None]:
    metadata = record.get("metadata") or {}
    country = str(metadata.get("country", "US")).upper()
    # Domestic baseline is US; non-US settlement legs carry elevated risk.
    if country not in {"US"}:
        return 15, f"cross_border:{country}"
    return 0, None


def _wire_points(record: dict[str, Any]) -> tuple[int, str | None]:
    if str(record.get("transaction_type")) == "wire_transfer":
        return 10, "wire_transfer"
    return 0, None


def score_transaction(record: dict[str, Any]) -> dict[str, Any]:
    """Return ``record`` enriched with ``risk_score``, ``risk_band`` and reasons."""

    amount = parse_money(record["amount"])
    total = 0
    reasons: list[str] = []
    for points, reason in (
        _high_value_points(amount),
        _off_hours_points(str(record.get("timestamp", ""))),
        _cross_border_points(record),
        _wire_points(record),
    ):
        total += points
        if reason:
            reasons.append(reason)

    score = min(total, 100)
    if score >= REVIEW_THRESHOLD:
        band = "high"
        status = "fraud_review"
    elif score >= 25:
        band = "medium"
        status = "passed_fraud"
    else:
        band = "low"
        status = "passed_fraud"

    return {
        **record,
        "risk_score": score,
        "risk_band": band,
        "risk_reasons": reasons,
        "status": status,
    }


def process_message(message: dict[str, Any]) -> dict[str, Any]:
    """Score the inbound transaction and forward it to the compliance checker."""

    inbound = Message.from_dict(message)
    scored = score_transaction(inbound.data)
    outbound = Message(
        source_agent=AGENT_NAME,
        target_agent="compliance_checker",
        message_type="transaction",
        data=scored,
    )
    return outbound.to_dict()
