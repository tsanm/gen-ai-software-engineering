"""Task 4 (Additional Features) acceptance tests: A summary, B interest, C csv, D rate-limit."""
from conftest import create, deposit, transfer, withdrawal


def test_account_summary(client):
    """#16 Option A: totals, count, most-recent date for an account."""
    create(client, deposit(toAccount="ACC-AAAAA", amount=300))
    create(client, deposit(toAccount="ACC-AAAAA", amount=200))
    create(client, withdrawal(fromAccount="ACC-AAAAA", amount=50))

    r = client.get("/accounts/ACC-AAAAA/summary")
    assert r.status_code == 200
    s = r.json()
    assert float(s["totalDeposits"]) == 500.0
    assert float(s["totalWithdrawals"]) == 50.0
    assert s["transactionCount"] == 3
    assert s["mostRecentTransactionDate"]


def test_simple_interest(client):
    """#17 Option B: interest = balance * rate * days / 365; bad params -> 400."""
    create(client, deposit(toAccount="ACC-AAAAA", amount=1000))
    r = client.get("/accounts/ACC-AAAAA/interest?rate=0.05&days=365")
    assert r.status_code == 200
    body = r.json()
    assert float(body["interest"]) == 50.0  # 1000 * 0.05 * 365/365

    assert client.get("/accounts/ACC-AAAAA/interest?rate=abc&days=30").status_code == 400
    assert client.get("/accounts/ACC-AAAAA/interest?rate=0.05").status_code == 400


def test_transactions_csv_export_and_route_precedence(client):
    """#18 Option C: CSV export; also proves /export isn't swallowed by /{id}."""
    create(client, transfer())
    r = client.get("/transactions/export?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    lines = [ln for ln in r.text.splitlines() if ln.strip()]
    assert lines[0].lower().startswith("id,")  # header row
    assert len(lines) >= 2  # header + at least one data row


def test_rate_limiting_returns_429(make_client):
    """#19 Option D: exceeding the configured per-IP limit -> 429."""
    client = make_client(rate_limit_max=5, rate_limit_window_seconds=60)
    codes = [client.get("/transactions").status_code for _ in range(7)]
    assert 429 in codes
    assert codes.count(200) <= 5
