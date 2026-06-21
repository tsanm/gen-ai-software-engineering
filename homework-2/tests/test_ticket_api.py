"""Task 3 — API endpoint tests (11+ tests)."""
from conftest import create, ticket


def test_create_returns_201_with_generated_fields(client):
    body = create(client)
    assert body["id"]
    assert body["created_at"] and body["updated_at"]
    assert body["status"] == "new"
    assert body["resolved_at"] is None


def test_create_with_missing_required_field_returns_400(client):
    payload = ticket()
    del payload["customer_email"]
    r = client.post("/tickets", json=payload)
    assert r.status_code == 400
    assert r.json()["error"] == "Validation failed"
    assert any(d["field"] == "customer_email" for d in r.json()["details"])


def test_create_with_auto_classify_sets_category_and_priority(client):
    r = client.post(
        "/tickets?auto_classify=true",
        json=ticket(subject="Critical: can't access account",
                    description="This is critical, production down and I cannot access."))
    assert r.status_code == 201
    body = r.json()
    assert body["category"] == "account_access"
    assert body["priority"] == "urgent"
    assert 0.0 <= body["classification_confidence"] <= 1.0


def test_get_existing_ticket(client):
    created = create(client)
    r = client.get(f"/tickets/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_missing_ticket_returns_404_envelope(client):
    r = client.get("/tickets/does-not-exist")
    assert r.status_code == 404
    assert "error" in r.json()
    assert r.headers.get("X-Request-ID")


def test_list_empty(client):
    assert client.get("/tickets").json() == []


def test_list_returns_created_tickets(client):
    create(client)
    create(client)
    assert len(client.get("/tickets").json()) == 2


def test_update_partial_changes_only_given_fields(client):
    created = create(client)
    r = client.put(f"/tickets/{created['id']}", json={"assigned_to": "agent-9"})
    assert r.status_code == 200
    body = r.json()
    assert body["assigned_to"] == "agent-9"
    assert body["subject"] == created["subject"]
    assert body["updated_at"] >= created["updated_at"]


def test_update_to_resolved_sets_resolved_at(client):
    created = create(client)
    r = client.put(f"/tickets/{created['id']}", json={"status": "resolved"})
    assert r.status_code == 200
    assert r.json()["resolved_at"] is not None


def test_update_missing_returns_404(client):
    r = client.put("/tickets/nope", json={"status": "closed"})
    assert r.status_code == 404


def test_delete_then_get_is_404(client):
    created = create(client)
    assert client.delete(f"/tickets/{created['id']}").status_code == 204
    assert client.get(f"/tickets/{created['id']}").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/tickets/nope").status_code == 404


def test_combined_filter_by_category_and_priority(client):
    create(client, ticket(category="billing_question", priority="high"))
    create(client, ticket(category="billing_question", priority="low"))
    create(client, ticket(category="technical_issue", priority="high"))
    r = client.get("/tickets?category=billing_question&priority=high")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["category"] == "billing_question"
    assert rows[0]["priority"] == "high"
