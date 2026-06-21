"""Ticket use-cases (Tasks 1, 2, 5).

All business logic lives here; routes are thin adapters. The service owns id and
timestamp generation, filtering, and the classification workflow, and emits a structured
log line for every classification decision.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from src.errors import NotFound
from src.models import (
    Category,
    ClassificationResult,
    Priority,
    Status,
    Ticket,
    TicketCreate,
    TicketStore,
    TicketUpdate,
)
from src.services.classifier import classify

logger = logging.getLogger("support_api")

# Statuses that mean the ticket is finished, so `resolved_at` should be stamped.
_TERMINAL = {Status.resolved, Status.closed}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TicketService:
    def __init__(self, store: TicketStore,
                 clock: Callable[[], datetime] | None = None) -> None:
        self._store = store
        self._clock = clock or _utcnow

    # --- create ---------------------------------------------------------------
    def create(self, payload: TicketCreate, auto_classify: bool = False) -> Ticket:
        now = self._clock()
        ticket = Ticket(id=str(uuid4()), created_at=now, updated_at=now,
                        **payload.model_dump())
        if auto_classify:
            self._apply_classification(ticket)
        if ticket.status in _TERMINAL:
            ticket.resolved_at = now
        return self._store.add(ticket)

    # --- read -----------------------------------------------------------------
    def get(self, ticket_id: str) -> Ticket:
        ticket = self._store.get(ticket_id)
        if ticket is None:
            raise NotFound(f"Ticket {ticket_id} not found")
        return ticket

    def list(self, *, category: Category | None = None, priority: Priority | None = None,
             status: Status | None = None, assigned_to: str | None = None) -> list[Ticket]:
        wanted = {
            "category": category,
            "priority": priority,
            "status": status,
            "assigned_to": assigned_to,
        }
        active = {field: value for field, value in wanted.items() if value is not None}
        return [t for t in self._store.list()
                if all(getattr(t, field) == value for field, value in active.items())]

    # --- update / delete ------------------------------------------------------
    def update(self, ticket_id: str, payload: TicketUpdate) -> Ticket:
        ticket = self.get(ticket_id)
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(ticket, field, value)
        ticket.updated_at = self._clock()
        if ticket.status in _TERMINAL and ticket.resolved_at is None:
            ticket.resolved_at = ticket.updated_at
        if ticket.status not in _TERMINAL:
            ticket.resolved_at = None
        return ticket

    def delete(self, ticket_id: str) -> None:
        if not self._store.delete(ticket_id):
            raise NotFound(f"Ticket {ticket_id} not found")

    # --- classification (Task 2) ---------------------------------------------
    def auto_classify(self, ticket_id: str) -> ClassificationResult:
        ticket = self.get(ticket_id)
        return self._apply_classification(ticket)

    def _apply_classification(self, ticket: Ticket) -> ClassificationResult:
        result = classify(ticket.subject, ticket.description)
        ticket.category = result.category
        ticket.priority = result.priority
        ticket.classification_confidence = result.confidence
        logger.info(
            "classified ticket=%s category=%s priority=%s confidence=%.2f keywords=%s",
            ticket.id, result.category.value, result.priority.value,
            result.confidence, result.keywords_found)
        return result
