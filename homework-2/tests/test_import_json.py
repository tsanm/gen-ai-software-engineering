"""Task 3 — JSON import parsing tests (5 tests)."""
import json

from conftest import import_bytes, ticket


def test_valid_json_imports_all_rows(client, fixtures_dir):
    content = (fixtures_dir / "valid.json").read_bytes()
    r = import_bytes(client, "valid.json", content, fmt="json")
    assert r.status_code == 200
    assert r.json()["successful"] == 2


def test_invalid_json_syntax_is_rejected(client):
    r = import_bytes(client, "bad.json", b"{not valid json", fmt="json")
    assert r.status_code == 400
    assert "error" in r.json()


def test_json_not_an_array_is_rejected(client):
    r = import_bytes(client, "obj.json", b'{"foo": "bar"}', fmt="json")
    assert r.status_code == 400


def test_json_tickets_wrapper_is_supported(client):
    payload = json.dumps({"tickets": [ticket(customer_id="CUST-W")]})
    r = import_bytes(client, "wrap.json", payload, fmt="json")
    assert r.status_code == 200
    assert r.json()["successful"] == 1


def test_json_invalid_row_is_counted_as_failed(client):
    payload = json.dumps([ticket(), ticket(customer_email="bad")])
    r = import_bytes(client, "mixed.json", payload, fmt="json")
    summary = r.json()
    assert summary["total"] == 2
    assert summary["successful"] == 1
    assert summary["failed"] == 1
