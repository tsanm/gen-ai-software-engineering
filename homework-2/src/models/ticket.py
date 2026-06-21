"""Ticket domain entities, enums, and inbound payloads (Pydantic v2).

The spec models a ticket with fixed enum fields; Pydantic enforces the basic shape
(types, enum membership, string-length bounds, email format) for both the API and the
bulk-import path, so validation lives in exactly one place.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Category(str, Enum):
    account_access = "account_access"
    technical_issue = "technical_issue"
    billing_question = "billing_question"
    feature_request = "feature_request"
    bug_report = "bug_report"
    other = "other"


class Priority(str, Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


class Status(str, Enum):
    new = "new"
    in_progress = "in_progress"
    waiting_customer = "waiting_customer"
    resolved = "resolved"
    closed = "closed"


class Source(str, Enum):
    web_form = "web_form"
    email = "email"
    api = "api"
    chat = "chat"
    phone = "phone"


class DeviceType(str, Enum):
    desktop = "desktop"
    mobile = "mobile"
    tablet = "tablet"


class TicketMetadata(BaseModel):
    source: Source
    browser: str | None = None
    device_type: DeviceType


class TicketCreate(BaseModel):
    """Incoming POST body / one parsed import row."""

    customer_id: str = Field(min_length=1)
    customer_email: EmailStr
    customer_name: str = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    category: Category = Category.other
    priority: Priority = Priority.medium
    status: Status = Status.new
    assigned_to: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: TicketMetadata


class TicketUpdate(BaseModel):
    """PUT body — partial update; only the fields provided are changed."""

    customer_id: str | None = Field(default=None, min_length=1)
    customer_email: EmailStr | None = None
    customer_name: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    category: Category | None = None
    priority: Priority | None = None
    status: Status | None = None
    assigned_to: str | None = None
    tags: list[str] | None = None
    metadata: TicketMetadata | None = None


class Ticket(BaseModel):
    """Stored + returned ticket."""

    id: str
    customer_id: str
    customer_email: EmailStr
    customer_name: str
    subject: str
    description: str
    category: Category
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    assigned_to: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: TicketMetadata
    classification_confidence: float | None = None
