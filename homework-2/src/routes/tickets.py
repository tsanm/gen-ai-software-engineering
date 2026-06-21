"""/tickets routes (Tasks 1, 2, 5).

Thin adapters over ``TicketService`` and ``ImportService``; all domain logic, validation,
and classification live in the services.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile

from src.errors import ApiError
from src.models import (
    Category,
    ClassificationResult,
    ImportSummary,
    Priority,
    Status,
    Ticket,
    TicketCreate,
    TicketUpdate,
)
from src.routes.dependencies import get_import_service, get_ticket_service
from src.services import ImportService, TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])

_EXT_TO_FORMAT = {"csv": "csv", "json": "json", "xml": "xml"}


@router.post("", status_code=201)
def create_ticket(
    payload: TicketCreate,
    auto_classify: bool = Query(False),
    service: TicketService = Depends(get_ticket_service),
) -> Ticket:
    return service.create(payload, auto_classify=auto_classify)


# Declared BEFORE /{ticket_id} so "import" is not captured as an id.
@router.post("/import")
async def import_tickets(
    file: UploadFile = File(...),
    format: str | None = Query(None),
    auto_classify: bool = Query(False),
    service: ImportService = Depends(get_import_service),
) -> ImportSummary:
    content = await file.read()
    fmt = (format or _infer_format(file.filename)).lower()
    return service.import_file(content, fmt, auto_classify=auto_classify)


@router.get("")
def list_tickets(
    service: TicketService = Depends(get_ticket_service),
    category: Category | None = Query(None),
    priority: Priority | None = Query(None),
    status: Status | None = Query(None),
    assigned_to: str | None = Query(None),
) -> list[Ticket]:
    return service.list(category=category, priority=priority,
                        status=status, assigned_to=assigned_to)


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: str,
    service: TicketService = Depends(get_ticket_service),
) -> Ticket:
    return service.get(ticket_id)


@router.put("/{ticket_id}")
def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> Ticket:
    return service.update(ticket_id, payload)


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(
    ticket_id: str,
    service: TicketService = Depends(get_ticket_service),
) -> Response:
    service.delete(ticket_id)
    return Response(status_code=204)


@router.post("/{ticket_id}/auto-classify")
def auto_classify_ticket(
    ticket_id: str,
    service: TicketService = Depends(get_ticket_service),
) -> ClassificationResult:
    return service.auto_classify(ticket_id)


def _infer_format(filename: str | None) -> str:
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in _EXT_TO_FORMAT:
            return _EXT_TO_FORMAT[ext]
    raise ApiError(400, "Cannot determine import format", [
        {"field": "format",
         "message": "Provide ?format=csv|json|xml or upload a file with that extension"}])
