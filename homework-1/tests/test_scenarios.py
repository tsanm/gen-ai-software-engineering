"""Broader API scenarios: end-to-end flows, edge cases, HTTP semantics, error consistency.

These complement the per-task acceptance tests with the kind of exploratory cases a
manual API tester would try.
"""
import csv
import io

from conftest import create, deposit, transfer, withdrawal

# --- end-to-end flows ------------------------------------------------------

def test_transfer_lifecycle_updates_both_accounts(client):
    """A funded transfer moves balance from sender to receiver and shows in both views."""
    create(client, deposit(toAccount="ACC-AAAAA", amount=1000))
    create(client, transfer(fromAccount="ACC-AAAAA", toAccount="ACC-BBBBB", amount=400))

    assert float(client.get("/accounts/ACC-AAAAA/balance").json()["balance"]) == 600.0
    assert float(client.get("/accounts/ACC-BBBBB/balance").json()["balance"]) == 400.0
    # the transfer appears when filtering by either account
    assert len(client.get("/transactions?accountId=ACC-AAAAA&type=transfer").json()) == 1
    assert len(client.get("/transactions?accountId=ACC-BBBBB&type=transfer").json()) == 1


def test_unknown_account_has_zero_balance_and_empty_summary(client):
    assert float(client.get("/accounts/ACC-ZZZZZ/balance").json()["balance"]) == 0.0
    summary = client.get("/accounts/ACC-ZZZZZ/summary").json()
    assert summary["transactionCount"] == 0
    assert summary["mostRecentTransactionDate"] is None
    interest = client.get("/accounts/ACC-ZZZZZ/interest?rate=0.05&days=30").json()["interest"]
    assert float(interest) == 0.0


def test_duplicate_posts_create_distinct_transactions(client):
    a = create(client, transfer())
    b = create(client, transfer())
    assert a["id"] != b["id"]
    assert len(client.get("/transactions").json()) == 2


# --- input normalization / coercion ---------------------------------------

def test_currency_is_case_insensitive_and_normalized(client):
    body = create(client, transfer(currency="usd"))
    assert body["currency"] == "USD"


def test_amount_accepts_numeric_string(client):
    body = create(client, transfer(amount="100.50"))
    assert float(body["amount"]) == 100.50


def test_unknown_fields_are_ignored(client):
    payload = transfer()
    payload["note"] = "ignore me"
    assert client.post("/transactions", json=payload).status_code == 201


def test_lowercase_account_prefix_is_rejected(client):
    """Regex requires the literal 'ACC-' prefix; case matters."""
    r = client.post("/transactions", json=transfer(fromAccount="acc-12345"))
    assert r.status_code == 400


# --- HTTP semantics & error consistency ------------------------------------

def test_malformed_json_returns_400_envelope(client):
    r = client.post("/transactions", content="{not json",
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 400
    assert "error" in r.json()


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/no-such-endpoint")
    assert r.status_code == 404
    assert "error" in r.json()
    assert r.headers.get("X-Request-ID")


def test_method_not_allowed_uses_error_envelope(client):
    r = client.delete("/transactions")
    assert r.status_code == 405
    assert "error" in r.json()


def test_invalid_date_filter_returns_400(client):
    r = client.get("/transactions?from=not-a-date")
    assert r.status_code == 400
    assert "error" in r.json()


def test_inverted_date_range_yields_empty(client):
    create(client, transfer())
    r = client.get("/transactions?from=2999-01-01&to=2000-01-01")
    assert r.status_code == 200
    assert r.json() == []


# --- Task 4 feature edge cases ---------------------------------------------

def test_summary_counts_only_relevant_directions(client):
    create(client, deposit(toAccount="ACC-AAAAA", amount=100))
    create(client, transfer(fromAccount="ACC-AAAAA", toAccount="ACC-BBBBB", amount=30))
    s = client.get("/accounts/ACC-AAAAA/summary").json()
    # the outgoing transfer is not a "deposit" or "withdrawal" total, but is counted
    assert float(s["totalDeposits"]) == 100.0
    assert float(s["totalWithdrawals"]) == 0.0
    assert s["transactionCount"] == 2


def test_csv_export_is_parseable_and_complete(client):
    create(client, deposit(toAccount="ACC-AAAAA", amount=100))
    create(client, withdrawal(fromAccount="ACC-AAAAA", amount=25))
    r = client.get("/transactions/export?format=csv")
    assert r.status_code == 200

    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert len(rows) == 2
    assert set(rows[0]) == {"id", "fromAccount", "toAccount", "amount",
                            "currency", "type", "timestamp", "status"}
    assert {row["type"] for row in rows} == {"deposit", "withdrawal"}


def test_csv_export_empty_has_header_only(client):
    r = client.get("/transactions/export?format=csv")
    assert r.status_code == 200
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert rows == []


def test_unsupported_export_format_returns_400(client):
    r = client.get("/transactions/export?format=json")
    assert r.status_code == 400
    assert "error" in r.json()


def test_interest_scales_with_days_and_rate(client):
    create(client, deposit(toAccount="ACC-AAAAA", amount=1000))
    half_year = client.get("/accounts/ACC-AAAAA/interest?rate=0.10&days=182.5")
    # days is an int param; 182 days at 10% on 1000 -> ~49.86
    r = client.get("/accounts/ACC-AAAAA/interest?rate=0.10&days=182")
    assert r.status_code == 200
    assert round(float(r.json()["interest"]), 2) == round(1000 * 0.10 * 182 / 365, 2)
    assert half_year.status_code == 400  # non-integer days rejected


def test_root_endpoint(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()
