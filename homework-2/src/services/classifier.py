"""Auto-classification rules engine (Task 2).

Pure, deterministic, and transparent: classification is keyword-driven, returns the
keywords it matched and a human-readable reason, and never depends on external state.
The category rules and the priority keyword rules come straight from the spec.
"""
from __future__ import annotations

import re

from src.models import Category, ClassificationResult, Priority

# Category keyword signals. Order of this list is the tie-breaker when two categories
# match the same number of keywords (earlier wins) — e.g. a reproducible defect is a
# bug_report rather than a generic technical_issue.
CATEGORY_KEYWORDS: list[tuple[Category, list[str]]] = [
    (Category.account_access, [
        "can't access", "cannot access", "can not access", "login", "log in", "log-in",
        "sign in", "sign-in", "password", "2fa", "two-factor", "locked out",
        "account access", "reset password", "verification code"]),
    (Category.billing_question, [
        "billing", "invoice", "payment", "refund", "charge", "charged", "subscription",
        "credit card", "overcharged", "receipt"]),
    (Category.bug_report, [
        "steps to reproduce", "reproduce", "reproducible", "defect", "regression",
        "stack trace"]),
    (Category.feature_request, [
        "feature request", "feature", "enhancement", "suggestion", "would be nice",
        "please add", "it would be great", "request to add", "wish"]),
    (Category.technical_issue, [
        "error", "crash", "crashes", "bug", "not working", "doesn't work", "broken",
        "exception", "fails", "failure", "timeout", "500"]),
]

# Priority keyword rules (spec). Checked in this order; the first tier with any match wins.
PRIORITY_KEYWORDS: list[tuple[Priority, list[str]]] = [
    (Priority.urgent, ["can't access", "cannot access", "can not access", "critical",
                       "production down", "security"]),
    (Priority.high, ["important", "blocking", "asap"]),
    (Priority.low, ["minor", "cosmetic", "suggestion"]),
]


def _compile(groups):
    """Pre-compile each keyword as a whole-token regex so it cannot match inside another
    word (e.g. 'security' must not match 'insecurity', '500' must not match '1500')."""
    return [(label, [(kw, re.compile(rf"\b{re.escape(kw)}\b")) for kw in keywords])
            for label, keywords in groups]


_CATEGORY_PATTERNS = _compile(CATEGORY_KEYWORDS)
_PRIORITY_PATTERNS = _compile(PRIORITY_KEYWORDS)


def _matches(text: str, patterns: list[tuple[str, re.Pattern]]) -> list[str]:
    """Return the keywords (in declaration order) that occur as whole tokens in the text."""
    return [kw for kw, pattern in patterns if pattern.search(text)]


def _classify_category(text: str) -> tuple[Category, list[str], float]:
    """Pick the best category by match count, tie-broken by declaration order."""
    best_cat = Category.other
    best_hits: list[str] = []
    for category, patterns in _CATEGORY_PATTERNS:
        hits = _matches(text, patterns)
        if len(hits) > len(best_hits):
            best_cat, best_hits = category, hits
    if not best_hits:
        return Category.other, [], 0.3
    confidence = min(0.95, 0.6 + 0.12 * len(best_hits))
    return best_cat, best_hits, confidence


def _classify_priority(text: str) -> tuple[Priority, list[str], float]:
    """Pick priority from the first matching tier; default to medium."""
    for priority, patterns in _PRIORITY_PATTERNS:
        hits = _matches(text, patterns)
        if hits:
            return priority, hits, 0.9
    return Priority.medium, [], 0.5


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def classify(subject: str, description: str) -> ClassificationResult:
    """Classify a ticket's category and priority from its subject and description."""
    text = f"{subject}\n{description}".lower()
    category, cat_hits, cat_conf = _classify_category(text)
    priority, pri_hits, pri_conf = _classify_priority(text)

    keywords_found = _dedupe(cat_hits + pri_hits)
    confidence = round((cat_conf + pri_conf) / 2, 2)
    reasoning = _build_reasoning(category, cat_hits, priority, pri_hits)

    return ClassificationResult(
        category=category,
        priority=priority,
        confidence=confidence,
        reasoning=reasoning,
        keywords_found=keywords_found,
    )


def _build_reasoning(category: Category, cat_hits: list[str],
                     priority: Priority, pri_hits: list[str]) -> str:
    if cat_hits:
        cat_part = (f"Category '{category.value}' from signals: "
                    f"{', '.join(repr(k) for k in cat_hits)}.")
    else:
        cat_part = "No strong category signals; defaulting to 'other'."
    if pri_hits:
        pri_part = (f" Priority '{priority.value}' from keywords: "
                    f"{', '.join(repr(k) for k in pri_hits)}.")
    else:
        pri_part = " Priority 'medium' (no priority keywords matched)."
    return cat_part + pri_part
