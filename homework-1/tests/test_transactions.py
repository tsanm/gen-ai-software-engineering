"""Task 1 (Core API) acceptance tests + sample-request parity."""
from conftest import create, deposit, transfer, withdrawal


def test_create_transaction_returns_201_with_generated_fields(client):
    """#1 POST creates a transaction with auto id, server timestamp, status."""
    body = create(client, transfer())
    assert body["id"]  # auto-generated, non-empty
    assert len(body["id"]) >= 16  # UUID-like
    assert body["fromAccount"] == "ACC-12345"
    assert body["toAccount"] == "ACC-67890"
    assert float(body["amount"]) == 100.50
    assert body["currency"] == "USD"
    assert body["type"] == "transfer"
    assert body["status"] == "completed"
    assert body["timestamp"]  # ISO-8601 server timestamp
    assert "T" in body["timestamp"]


def test_list_transactions_returns_all(client):
    """#2 GET /transactions returns every created transaction."""
    create(client, transfer())
    create(client, deposit())
    r = client.get("/transactions")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_transaction_by_id_and_404(client):
    """#3 GET /transactions/:id returns the txn; unknown id -> 404."""
    created = create(client, transfer())
    r = client.get(f"/transactions/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]

    missing = client.get("/transactions/does-not-exist")
    assert missing.status_code == 404


def test_balance_computed_from_completed_transactions(client):
    """#4 Balance = deposits(+) - withdrawals(-) +/- transfers, completed only."""
    create(client, deposit(toAccount="ACC-AAAAA", amount=1000.00))
    create(client, withdrawal(fromAccount="ACC-AAAAA", amount=250.00))
    create(client, transfer(fromAccount="ACC-AAAAA", toAccount="ACC-BBBBB", amount=100.00))
    create(client, transfer(fromAccount="ACC-CCCCC", toAccount="ACC-AAAAA", amount=50.00))

    r = client.get("/accounts/ACC-AAAAA/balance")
    assert r.status_code == 200
    # 1000 - 250 - 100 + 50 = 700
    assert float(r.json()["balance"]) == 700.00


def test_create_with_non_positive_amount_rejected(client):
    """#5 Amounts must be positive."""
    assert client.post("/transactions", json=transfer(amount=0)).status_code == 400
    assert client.post("/transactions", json=transfer(amount=-10)).status_code == 400


def test_sample_requests_from_tasks_md_parity(client):
    """#15 The exact sample payload documented in TASKS.md must succeed."""
    r = client.post("/transactions", json={
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.50,
        "currency": "USD",
        "type": "transfer",
    })
    assert r.status_code == 201
    assert client.get("/transactions").status_code == 200
    assert client.get("/transactions?accountId=ACC-12345").status_code == 200
    assert client.get("/accounts/ACC-12345/balance").status_code == 200
