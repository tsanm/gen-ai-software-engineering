"""Task 2 (Validation) acceptance tests.

All validation failures must return HTTP 400 with the documented shape:
    {"error": "Validation failed", "details": [{"field": ..., "message": ...}]}
"""
from conftest import deposit, transfer


def _details(resp):
    body = resp.json()
    assert body["error"] == "Validation failed"
    return {d["field"] for d in body["details"]}, body["details"]


def test_negative_amount_has_amount_detail(client):
    """#6a Non-positive amount -> 400 with field=amount."""
    r = client.post("/transactions", json=transfer(amount=-5))
    assert r.status_code == 400
    fields, _ = _details(r)
    assert "amount" in fields


def test_too_many_decimals_for_usd(client):
    """#6b USD allows 2 decimals; 3 decimals -> 400 field=amount."""
    r = client.post("/transactions", json=transfer(amount=100.123))
    assert r.status_code == 400
    fields, _ = _details(r)
    assert "amount" in fields


def test_invalid_account_format(client):
    """#7 Account not matching ACC-XXXXX -> 400 with account field."""
    r = client.post("/transactions", json=transfer(fromAccount="12345"))
    assert r.status_code == 400
    fields, _ = _details(r)
    assert "fromAccount" in fields


def test_invalid_currency_code(client):
    """#8 Unknown ISO 4217 code -> 400 field=currency."""
    r = client.post("/transactions", json=transfer(currency="XYZ"))
    assert r.status_code == 400
    fields, _ = _details(r)
    assert "currency" in fields


def test_multiple_validation_errors_aggregated(client):
    """#9 Several bad fields -> 400 with >=2 detail entries (spec example shape)."""
    r = client.post("/transactions", json=transfer(amount=-1, currency="XYZ"))
    assert r.status_code == 400
    fields, details = _details(r)
    assert {"amount", "currency"} <= fields
    assert len(details) >= 2
    for d in details:
        assert "field" in d and "message" in d


def test_per_type_field_rules(client):
    """#10 Each type needs its essential account; transfer accounts must differ; any
    provided account must be well-formed. Presence of an extra account is allowed
    (the spec models both fields as strings for every type)."""
    # deposit requires a destination account
    no_dest = {"amount": 10, "currency": "USD", "type": "deposit"}
    assert client.post("/transactions", json=no_dest).status_code == 400
    # withdrawal requires a source account
    no_source = {"amount": 10, "currency": "USD", "type": "withdrawal"}
    assert client.post("/transactions", json=no_source).status_code == 400
    # transfer source and destination must differ
    same_acct = transfer(fromAccount="ACC-12345", toAccount="ACC-12345")
    assert client.post("/transactions", json=same_acct).status_code == 400
    # a provided account must match the format, regardless of type
    assert client.post("/transactions", json=deposit(toAccount="bad")).status_code == 400

    # a deposit that also carries a (valid) fromAccount is accepted - spec allows it
    ok = {"fromAccount": "ACC-12345", "toAccount": "ACC-67890",
          "amount": 10, "currency": "USD", "type": "deposit"}
    assert client.post("/transactions", json=ok).status_code == 201


def test_blank_account_treated_as_absent(client):
    """Regression: empty/whitespace account strings normalize to absent, not stored as ''."""
    # blank fromAccount on a deposit is ignored -> accepted
    body = {"fromAccount": "  ", "toAccount": "ACC-12345",
            "amount": 10, "currency": "USD", "type": "deposit"}
    created = client.post("/transactions", json=body)
    assert created.status_code == 201
    assert created.json()["fromAccount"] is None
    # blank source on a transfer counts as missing -> rejected
    bad = transfer(fromAccount="")
    assert client.post("/transactions", json=bad).status_code == 400


def test_garbage_type_still_returns_400_shape(client):
    """Unknown enum value is reformatted into the same 400 envelope."""
    r = client.post("/transactions", json=transfer(type="bogus"))
    assert r.status_code == 400
    assert r.json()["error"] == "Validation failed"
