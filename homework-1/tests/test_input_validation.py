"""Input-validation tests for account-scoped queries.

A banking API must reject malformed input at the edge rather than silently returning a
zero result. These cover the account-id and interest-parameter validation added in the
application service.
"""
from conftest import create, deposit, transfer


def _details(resp):
    body = resp.json()
    assert body["error"] == "Validation failed"
    return {d["field"] for d in body["details"]}


def test_balance_rejects_malformed_account_id(client):
    r = client.get("/accounts/not-an-account/balance")
    assert r.status_code == 400
    assert "accountId" in _details(r)


def test_summary_rejects_malformed_account_id(client):
    r = client.get("/accounts/12345/summary")
    assert r.status_code == 400
    assert "accountId" in _details(r)


def test_interest_rejects_malformed_account_id(client):
    r = client.get("/accounts/bad/interest?rate=0.05&days=30")
    assert r.status_code == 400
    assert "accountId" in _details(r)


def test_interest_rejects_negative_rate(client):
    create(client, deposit(toAccount="ACC-AAAAA", amount=1000))
    r = client.get("/accounts/ACC-AAAAA/interest?rate=-0.05&days=30")
    assert r.status_code == 400
    assert "rate" in _details(r)


def test_interest_rejects_negative_days(client):
    create(client, deposit(toAccount="ACC-AAAAA", amount=1000))
    r = client.get("/accounts/ACC-AAAAA/interest?rate=0.05&days=-30")
    assert r.status_code == 400
    assert "days" in _details(r)


def test_valid_account_still_succeeds(client):
    """Sanity: a well-formed (even if unknown) account id passes validation -> 200."""
    assert client.get("/accounts/ACC-ZZZZZ/balance").status_code == 200
    assert client.get("/accounts/ACC-ZZZZZ/summary").status_code == 200
    assert client.get("/accounts/ACC-ZZZZZ/interest?rate=0.05&days=30").status_code == 200


# --- regression: finite-but-huge / non-finite inputs must 400, never 500 ----

def test_huge_amount_string_rejected_not_500(client):
    """Regression: a finite huge amount must not crash quantize() -> 400, field=amount."""
    r = client.post("/transactions", json=transfer(amount="1E999"))
    assert r.status_code == 400
    assert "amount" in _details(r)


def test_huge_integer_amount_rejected(client):
    """Regression: a many-digit integer amount must be rejected, not 500."""
    r = client.post("/transactions", json=transfer(amount="1" + "0" * 400))
    assert r.status_code == 400
    assert "amount" in _details(r)


def test_huge_amount_rejected_for_zero_decimal_currency(client):
    """Regression: the quantize overflow also occurs for 0-minor-unit currencies (JPY)."""
    r = client.post("/transactions", json=transfer(currency="JPY", amount="1E999"))
    assert r.status_code == 400
    assert "amount" in _details(r)


def test_non_finite_interest_rate_rejected_not_500(client):
    """Regression: rate coerced to inf must 400 (finite check), not serialize Infinity -> 500."""
    create(client, deposit(toAccount="ACC-AAAAA", amount=1000))
    r = client.get("/accounts/ACC-AAAAA/interest?rate=1e400&days=30")
    assert r.status_code == 400
    assert "rate" in _details(r)
