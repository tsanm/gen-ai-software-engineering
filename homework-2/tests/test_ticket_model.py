"""Task 3 — data validation tests for the Ticket models (9 tests)."""
import pytest
from conftest import ticket
from pydantic import ValidationError

from src.models import Category, Priority, Status, TicketCreate


def test_valid_payload_builds_with_defaults():
    model = TicketCreate.model_validate(ticket())
    assert model.category == Category.other
    assert model.priority == Priority.medium
    assert model.status == Status.new
    assert model.tags == []


def test_invalid_email_is_rejected():
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(ticket(customer_email="not-an-email"))


def test_subject_too_long_is_rejected():
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(ticket(subject="x" * 201))


def test_subject_empty_is_rejected():
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(ticket(subject=""))


def test_description_too_short_is_rejected():
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(ticket(description="short"))


def test_description_too_long_is_rejected():
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(ticket(description="y" * 2001))


def test_boundary_lengths_are_accepted():
    model = TicketCreate.model_validate(
        ticket(subject="s" * 200, description="d" * 2000))
    assert len(model.subject) == 200
    assert len(model.description) == 2000


@pytest.mark.parametrize("field,value", [
    ("category", "not_a_category"),
    ("priority", "super_urgent"),
    ("status", "archived"),
])
def test_invalid_enum_values_are_rejected(field, value):
    with pytest.raises(ValidationError):
        TicketCreate.model_validate(ticket(**{field: value}))


@pytest.mark.parametrize("meta", [
    {"browser": "Chrome", "device_type": "desktop"},          # missing source
    {"source": "web_form", "device_type": "desktop", "x": 1}, # ok-ish but bad device below
    {"source": "telegram", "device_type": "desktop"},         # invalid source enum
    {"source": "web_form", "device_type": "watch"},           # invalid device enum
])
def test_invalid_metadata_is_rejected(meta):
    # The second case is actually valid; assert the genuinely-invalid ones raise.
    if meta.get("source") == "web_form" and meta.get("device_type") == "desktop":
        TicketCreate.model_validate(ticket(metadata=meta))  # should not raise
    else:
        with pytest.raises(ValidationError):
            TicketCreate.model_validate(ticket(metadata=meta))
