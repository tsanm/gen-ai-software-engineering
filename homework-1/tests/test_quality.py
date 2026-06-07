"""Cross-cutting tests: reliability, observability, multi-region extensibility, compliance."""
from decimal import Decimal

from conftest import create, deposit, transfer


def test_consistent_error_envelope_for_404_and_429(make_client):
    """#20 404 and 429 use the same {error, ...} envelope as 400."""
    client = make_client(rate_limit_max=2)
    nf = client.get("/transactions/nope")
    assert nf.status_code == 404
    assert "error" in nf.json()

    codes = [client.get("/health").status_code for _ in range(1)]  # health is exempt
    assert codes == [200]

    # exhaust the limit on a non-exempt path
    last = None
    for _ in range(5):
        last = client.get("/transactions")
    assert last.status_code == 429
    assert "error" in last.json()


def test_internal_error_is_safe(make_client, monkeypatch):
    """#21 An unexpected failure -> generic 500 body, no traceback leaked."""
    import src.services as services
    client = make_client()

    def boom(*a, **k):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(services, "filter_transactions", boom)
    r = client.get("/transactions")
    assert r.status_code == 500
    body = r.json()
    assert "error" in body
    assert "secret internal detail" not in r.text
    assert "Traceback" not in r.text
    assert r.headers.get("X-Request-ID")  # request-id present even on 500s


def test_request_id_header_present(client):
    """#22 Every response carries an X-Request-ID; errors echo it in the body."""
    ok = client.get("/transactions")
    assert ok.headers.get("X-Request-ID")

    nf = client.get("/transactions/nope")
    assert nf.headers.get("X-Request-ID")
    assert nf.json().get("requestId") == nf.headers["X-Request-ID"]


def test_health_and_docs_available(client):
    """#23 Health check + Swagger UI are reachable."""
    assert client.get("/health").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_currency_aware_precision(make_client):
    """#24 Precision is driven by ISO-4217 minor units, not a hardcoded 2."""
    client = make_client()
    # JPY has 0 minor units -> any fractional part is invalid
    jpy_frac = client.post("/transactions", json=transfer(currency="JPY", amount=100.5))
    assert jpy_frac.status_code == 400
    jpy_whole = client.post("/transactions", json=transfer(currency="JPY", amount=100))
    assert jpy_whole.status_code == 201
    # BHD has 3 minor units -> 3 decimals allowed
    bhd = client.post("/transactions", json=transfer(currency="BHD", amount=100.123))
    assert bhd.status_code == 201


def test_money_precision_no_float_drift(client):
    """#25 Amounts are Decimal-backed; sums don't accumulate binary float error."""
    create(client, deposit(toAccount="ACC-AAAAA", amount=0.10))
    create(client, deposit(toAccount="ACC-AAAAA", amount=0.20))
    r = client.get("/accounts/ACC-AAAAA/balance")
    assert Decimal(str(r.json()["balance"])) == Decimal("0.30")


def test_compliance_audit_trail(make_client):
    """#26 Every create is audited; over-threshold txns raise a compliance flag."""
    client = make_client(large_amount_threshold=Decimal("1000"))
    audit = client.app.state.audit

    create(client, deposit(toAccount="ACC-AAAAA", amount=50))
    assert any(e["action"] == "transaction.created" for e in audit.entries)

    create(client, deposit(toAccount="ACC-AAAAA", amount=5000))  # over threshold
    assert any(e["action"] == "compliance.flagged" for e in audit.entries)

    # PII is masked in the audit metadata (no full account number persisted)
    accounts_in_audit = [str(e.get("metadata", {})) for e in audit.entries]
    assert not any("ACC-AAAAA" in s for s in accounts_in_audit)
