"""FastAPI dependency providers.

Services are built once per app and stored on ``app.state`` (see ``create_app``); these
providers expose them to routes so handlers stay thin and tests can swap app state.
"""
from __future__ import annotations

from fastapi import Request

from src.services import ImportService, TicketService


def get_ticket_service(request: Request) -> TicketService:
    return request.app.state.ticket_service


def get_import_service(request: Request) -> ImportService:
    return request.app.state.import_service
