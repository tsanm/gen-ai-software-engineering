"""Task 3 (Transaction History / filtering) acceptance tests."""
from conftest import create, deposit, transfer, withdrawal


def _seed(client):
    create(client, deposit(toAccount="ACC-AAAAA", amount=100, currency="USD"))
    create(client, withdrawal(fromAccount="ACC-AAAAA", amount=20, currency="USD"))
    create(client, transfer(fromAccount="ACC-AAAAA", toAccount="ACC-BBBBB", amount=30))
    create(client, transfer(fromAccount="ACC-CCCCC", toAccount="ACC-DDDDD", amount=40))


def test_filter_by_account_matches_sender_or_receiver(client):
    """#11 ?accountId returns txns where the account is sender OR receiver."""
    _seed(client)
    r = client.get("/transactions?accountId=ACC-AAAAA")
    assert r.status_code == 200
    rows = r.json()
    # deposit-in, withdrawal-out, transfer-out  => 3 of the 4 involve ACC-AAAAA
    assert len(rows) == 3
    for row in rows:
        assert "ACC-AAAAA" in (row.get("fromAccount"), row.get("toAccount"))


def test_filter_by_type(client):
    """#12 ?type=transfer returns only transfers."""
    _seed(client)
    r = client.get("/transactions?type=transfer")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    assert all(row["type"] == "transfer" for row in rows)


def test_filter_by_date_range(client):
    """#13 ?from&to filter on timestamp (today's txns fall inside today's range)."""
    _seed(client)
    inside = client.get("/transactions?from=2000-01-01&to=2999-12-31")
    assert inside.status_code == 200
    assert len(inside.json()) == 4

    outside = client.get("/transactions?from=2000-01-01&to=2000-01-02")
    assert outside.status_code == 200
    assert len(outside.json()) == 0


def test_combined_filters_intersect(client):
    """#14 accountId + type combine (AND semantics)."""
    _seed(client)
    r = client.get("/transactions?accountId=ACC-AAAAA&type=transfer")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["type"] == "transfer"
    assert rows[0]["fromAccount"] == "ACC-AAAAA"
