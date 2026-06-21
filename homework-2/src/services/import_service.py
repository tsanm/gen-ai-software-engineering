"""Bulk import orchestration (Task 1).

Parses a CSV/JSON/XML file into rows, validates each row independently, and creates the
valid ones — returning a summary of total / successful / failed with per-row error detail.
One bad row never aborts the whole import; a malformed *file* is rejected up front (400).
"""
from __future__ import annotations

import logging

from pydantic import ValidationError

from src.errors import ApiError
from src.models import ImportSummary, RowError, TicketCreate
from src.services.parsers import parse_records
from src.services.ticket_service import TicketService

logger = logging.getLogger("support_api")


class ImportService:
    def __init__(self, tickets: TicketService, *, max_records: int = 1000,
                 max_bytes: int = 5_000_000) -> None:
        self._tickets = tickets
        self._max_records = max_records
        self._max_bytes = max_bytes

    def import_file(self, content: bytes, fmt: str,
                    auto_classify: bool = False) -> ImportSummary:
        if len(content) > self._max_bytes:
            raise ApiError(413, "Import file too large", [
                {"field": None,
                 "message": f"File exceeds the {self._max_bytes}-byte limit"}])

        rows = parse_records(content, fmt)
        if len(rows) > self._max_records:
            raise ApiError(413, "Too many records", [
                {"field": None,
                 "message": f"Import exceeds the {self._max_records}-record limit"}])

        summary = ImportSummary(total=len(rows), successful=0, failed=0)
        for index, raw in enumerate(rows):
            self._import_row(index, raw, auto_classify, summary)
        logger.info("import fmt=%s total=%d ok=%d failed=%d",
                    fmt, summary.total, summary.successful, summary.failed)
        return summary

    def _import_row(self, index: int, raw: dict, auto_classify: bool,
                    summary: ImportSummary) -> None:
        try:
            payload = TicketCreate.model_validate(raw)
        except ValidationError as exc:
            summary.failed += 1
            summary.errors.append(RowError(row=index, errors=_details(exc)))
            return
        ticket = self._tickets.create(payload, auto_classify=auto_classify)
        summary.successful += 1
        summary.created_ids.append(ticket.id)


def _details(exc: ValidationError) -> list[dict]:
    """Render Pydantic errors as the documented {field, message} detail list."""
    out: list[dict] = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", ()) if p not in ("body",)]
        out.append({"field": ".".join(loc) or None, "message": err.get("msg", "Invalid")})
    return out
