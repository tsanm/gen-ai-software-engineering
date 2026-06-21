"""Unified error model so every failure (400/404/429/500) shares one envelope:

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


class ValidationProblem(ApiError):
    """400 with the documented validation shape."""

    def __init__(self, details: list[dict]) -> None:
        super().__init__(400, "Validation failed", details)


def error_body(error: str, request_id: str | None,
               details: list[dict] | None = None) -> dict:
    body: dict = {"error": error}
    if details is not None:
        body["details"] = details
    if request_id is not None:
        body["requestId"] = request_id
    return body
