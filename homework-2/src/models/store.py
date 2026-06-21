"""In-memory ticket store (data-access layer).

Encapsulated behind a tiny interface so the persistence mechanism can be swapped for a
real database later without touching routes or services. One instance per app (app.state).
"""
from __future__ import annotations

from src.models.ticket import Ticket


class TicketStore:
    def __init__(self) -> None:
        self._by_id: dict[str, Ticket] = {}

    def add(self, ticket: Ticket) -> Ticket:
        self._by_id[ticket.id] = ticket
        return ticket

    def get(self, ticket_id: str) -> Ticket | None:
        return self._by_id.get(ticket_id)

    def list(self) -> list[Ticket]:
        return list(self._by_id.values())

    def delete(self, ticket_id: str) -> bool:
        return self._by_id.pop(ticket_id, None) is not None
