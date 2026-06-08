"""Task 3 — auto-classification tests (10 tests)."""
import pytest
from conftest import create, ticket

from src.services.classifier import classify


@pytest.mark.parametrize("subject,description,expected", [
    ("Cannot log in", "I forgot my password and can't access my account.", "account_access"),
    ("App error", "The app keeps throwing an error and then crashes.", "technical_issue"),
    ("Invoice problem", "I need a refund for a duplicate billing charge.", "billing_question"),
    ("Idea", "Feature request: it would be nice to add a dark mode.", "feature_request"),
    ("Defect", "Here are the steps to reproduce the defect every time.", "bug_report"),
])
def test_category_rules(subject, description, expected):
    assert classify(subject, description).category.value == expected


def test_no_signal_defaults_to_other_with_low_confidence():
    result = classify("Hello", "Just saying hi to the wonderful team today.")
    assert result.category.value == "other"
    assert result.confidence <= 0.4


@pytest.mark.parametrize("text,expected", [
    ("This is critical, production down right now", "urgent"),
    ("This is important and blocking, please fix asap", "high"),
    ("A minor cosmetic issue", "low"),
    ("Just a general question about usage", "medium"),
])
def test_priority_rules(text, expected):
    assert classify("subject", text).priority.value == expected


def test_result_shape_is_valid():
    result = classify("Critical login bug", "Can't access account, this is critical.")
    assert 0.0 <= result.confidence <= 1.0
    assert result.keywords_found
    assert isinstance(result.reasoning, str) and result.reasoning


def test_auto_classify_endpoint_updates_and_stores(client):
    created = create(client, ticket(
        subject="Critical outage", description="Production down, this is critical."))
    r = client.post(f"/tickets/{created['id']}/auto-classify")
    assert r.status_code == 200
    body = r.json()
    assert body["priority"] == "urgent"
    assert set(body) >= {"category", "priority", "confidence", "reasoning", "keywords_found"}
    # confidence is persisted on the ticket
    stored = client.get(f"/tickets/{created['id']}").json()
    assert stored["classification_confidence"] == body["confidence"]


def test_auto_classify_missing_ticket_returns_404(client):
    assert client.post("/tickets/nope/auto-classify").status_code == 404


@pytest.mark.parametrize("word", ["insecurity", "terror", "recharge", "1500 dollars"])
def test_keywords_do_not_match_inside_other_words(word):
    """Whole-token matching: 'security' must not fire on 'insecurity', etc."""
    result = classify("General note", f"This is just a comment about {word} here, nothing else.")
    assert result.category.value == "other"
    assert result.priority.value == "medium"
    assert result.keywords_found == []


def test_can_not_access_spelling_is_urgent():
    """All three spellings of 'cannot access' raise priority to urgent (spec parity)."""
    for phrasing in ["can't access", "cannot access", "can not access"]:
        assert classify("Help", f"I {phrasing} my account.").priority.value == "urgent"
