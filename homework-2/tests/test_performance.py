"""Task 5 — performance benchmarks (5 tests).

Thresholds are deliberately generous so the suite is not flaky on slow CI, while still
catching pathological (e.g. accidentally quadratic) regressions.
"""
import io
import time

from conftest import create, import_bytes, ticket


def _csv_with_rows(n: int) -> bytes:
    buf = io.StringIO()
    buf.write("customer_id,customer_email,customer_name,subject,description,"
              "source,device_type\n")
    for i in range(n):
        buf.write(f"C{i},user{i}@example.com,User {i},Subject {i},"
                  f"This is a sufficiently long description number {i}.,web_form,desktop\n")
    return buf.getvalue().encode("utf-8")


def test_create_many_tickets_is_fast(client):
    start = time.monotonic()
    for i in range(200):
        create(client, ticket(customer_id=f"C{i}"))
    assert time.monotonic() - start < 10.0


def test_bulk_import_500_rows_is_fast(client):
    start = time.monotonic()
    r = import_bytes(client, "big.csv", _csv_with_rows(500), fmt="csv")
    elapsed = time.monotonic() - start
    assert r.json()["successful"] == 500
    assert elapsed < 10.0


def test_listing_scales_linearly(client):
    import_bytes(client, "big.csv", _csv_with_rows(500), fmt="csv")
    start = time.monotonic()
    assert len(client.get("/tickets").json()) == 500
    assert time.monotonic() - start < 3.0


def test_filtered_listing_is_fast(client):
    import_bytes(client, "big.csv", _csv_with_rows(500), fmt="csv")
    start = time.monotonic()
    client.get("/tickets?category=other&priority=medium")
    assert time.monotonic() - start < 3.0


def test_classification_is_fast(client):
    created = create(client, ticket(description="A" * 1900 + " critical outage"))
    start = time.monotonic()
    for _ in range(100):
        client.post(f"/tickets/{created['id']}/auto-classify")
    assert time.monotonic() - start < 5.0
