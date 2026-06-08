"""Cross-cutting tests: one error envelope, request-id propagation, safe 500s, ops."""
from conftest import create, ticket


def test_consistent_error_envelope_for_404_and_validation(client):
    nf = client.get("/tickets/nope")
    assert nf.status_code == 404
    assert "error" in nf.json()

    bad = client.post("/tickets", json={"customer_id": "x"})  # missing required fields
    assert bad.status_code == 400
    body = bad.json()
    assert body["error"] == "Validation failed"
    assert isinstance(body["details"], list) and body["details"]


def test_internal_error_is_safe(client, monkeypatch):
    """An unexpected failure -> generic 500 body, no traceback or secret leaked."""
    def boom(*a, **k):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(client.app.state.ticket_service, "list", boom)
    r = client.get("/tickets")
    assert r.status_code == 500
    assert "error" in r.json()
    assert "secret internal detail" not in r.text
    assert "Traceback" not in r.text
    assert r.headers.get("X-Request-ID")


def test_request_id_present_and_echoed(client):
    ok = client.get("/tickets")
    assert ok.headers.get("X-Request-ID")

    nf = client.get("/tickets/nope")
    assert nf.headers.get("X-Request-ID")
    assert nf.json().get("requestId") == nf.headers["X-Request-ID"]


def test_health_and_docs_available(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/").json()["name"]


def test_unsupported_import_format_is_rejected(client):
    r = client.post(
        "/tickets/import?format=yaml",
        files={"file": ("x.yaml", b"nope", "application/octet-stream")})
    assert r.status_code == 400
    assert "error" in r.json()


def test_create_ticket_with_explicit_classification_workflow(client):
    """A created ticket starts unclassified; auto-classify then populates confidence."""
    created = create(client, ticket())
    assert created["classification_confidence"] is None
    client.post(f"/tickets/{created['id']}/auto-classify")
    assert client.get(f"/tickets/{created['id']}").json()["classification_confidence"] is not None
