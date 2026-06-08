"""Transport-agnostic view models / DTOs returned by services.

Keeping these separate from the stored entity means a service result is the same object
whether it is driven by the HTTP layer, a CLI, or a queue consumer.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.models.ticket import Category, Priority


class RowError(BaseModel):
    """One failed record in a bulk import."""

    row: int
    errors: list[dict]


class ImportSummary(BaseModel):
    """Result of a bulk import (Task 1)."""

    total: int
    successful: int
    failed: int
    created_ids: list[str] = Field(default_factory=list)
    errors: list[RowError] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    """Result of auto-classification (Task 2)."""

    category: Category
    priority: Priority
    confidence: float
    reasoning: str
    keywords_found: list[str] = Field(default_factory=list)
