"""Unified error model so every failure (400/404/422/500) shares one envelope:

    {"error": "...", "details": [{"field": ..., "message": ...}], "requestId": "..."}
"""
from __future__ import annotations


class ApiError(Exception):
    """Raised by routes/services; rendered by the central exception handler."""

    def __init__(self, status_code: int, error: str,
                 details: list[dict] | None = None) -> None:
        super().__init__(error)
        self.status_code = status_code
        self.error = error
        self.details = details


class NotFound(ApiError):
    """404 for a missing resource."""

    def __init__(self, message: str) -> None:
        super().__init__(404, message)


def error_body(error: str, request_id: str | None,
               details: list[dict] | None = None) -> dict:
    body: dict = {"error": error}
    if details is not None:
        body["details"] = details
    if request_id is not None:
        body["requestId"] = request_id
    return body
