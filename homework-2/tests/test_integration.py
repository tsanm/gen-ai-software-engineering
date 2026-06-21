"""Task 5 — end-to-end integration tests (5 tests)."""
from concurrent.futures import ThreadPoolExecutor

from conftest import create, import_bytes, ticket


def test_full_ticket_lifecycle(client):
    created = create(client)
    tid = created["id"]
    assert client.get(f"/tickets/{tid}").status_code == 200

    client.put(f"/tickets/{tid}", json={"status": "in_progress", "assigned_to": "agent-1"})
    resolved = client.put(f"/tickets/{tid}", json={"status": "resolved"}).json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None

    # reopening clears the resolution timestamp
    reopened = client.put(f"/tickets/{tid}", json={"status": "in_progress"}).json()
    assert reopened["resolved_at"] is None

    assert client.delete(f"/tickets/{tid}").status_code == 204
    assert client.get(f"/tickets/{tid}").status_code == 404


def test_bulk_import_with_auto_classification(client, fixtures_dir):
    content = (fixtures_dir / "valid.csv").read_bytes()
    r = import_bytes(client, "valid.csv", content, fmt="csv", auto_classify=True)
    assert r.json()["successful"] == 3
    # Every imported ticket now carries a classification confidence.
    for t in client.get("/tickets").json():
        assert t["classification_confidence"] is not None
    # The crash ticket is classified as a technical issue.
    crash = next(t for t in client.get("/tickets").json() if t["customer_id"] == "CUST-102")
    assert crash["category"] == "technical_issue"


def test_concurrent_creates_are_all_persisted(client):
    def make_one(i):
        return client.post("/tickets", json=ticket(customer_id=f"CUST-{i}")).status_code

    with ThreadPoolExecutor(max_workers=10) as pool:
        codes = list(pool.map(make_one, range(25)))

    assert all(code == 201 for code in codes)
    ids = {t["id"] for t in client.get("/tickets").json()}
    assert len(ids) == 25  # 25 distinct tickets, no lost updates


def test_combined_filtering_by_category_and_priority(client):
    create(client, ticket(category="billing_question", priority="high"))
    create(client, ticket(category="billing_question", priority="urgent"))
    create(client, ticket(category="account_access", priority="high"))
    rows = client.get("/tickets?category=billing_question&priority=high").json()
    assert len(rows) == 1


def test_import_then_list_reflects_counts(client, fixtures_dir):
    import_bytes(client, "valid.json",
                 (fixtures_dir / "valid.json").read_bytes(), fmt="json")
    import_bytes(client, "valid.xml",
                 (fixtures_dir / "valid.xml").read_bytes(), fmt="xml")
    assert len(client.get("/tickets").json()) == 4
