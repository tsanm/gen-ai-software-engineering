"""Task 3 — CSV import parsing tests (6 tests)."""
from conftest import import_bytes


def test_valid_csv_imports_all_rows(client, fixtures_dir):
    content = (fixtures_dir / "valid.csv").read_bytes()
    r = import_bytes(client, "valid.csv", content, fmt="csv")
    assert r.status_code == 200
    summary = r.json()
    assert summary["total"] == 3
    assert summary["successful"] == 3
    assert summary["failed"] == 0
    assert len(client.get("/tickets").json()) == 3


def test_csv_invalid_row_is_reported_not_fatal(client, fixtures_dir):
    content = (fixtures_dir / "invalid_row.csv").read_bytes()
    r = import_bytes(client, "invalid_row.csv", content, fmt="csv")
    summary = r.json()
    assert summary["total"] == 2
    assert summary["successful"] == 1
    assert summary["failed"] == 1
    assert summary["errors"][0]["row"] == 1
    assert summary["errors"][0]["errors"]


def test_csv_non_utf8_is_rejected_gracefully(client):
    r = import_bytes(client, "bad.csv", b"\xff\xfe\x00bad", fmt="csv")
    assert r.status_code == 400
    assert "error" in r.json()


def test_csv_header_only_imports_nothing(client):
    header = "customer_id,customer_email,customer_name,subject,description,source,device_type\n"
    r = import_bytes(client, "empty.csv", header, fmt="csv")
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_csv_tags_are_split_into_list(client, fixtures_dir):
    content = (fixtures_dir / "valid.csv").read_bytes()
    import_bytes(client, "valid.csv", content, fmt="csv")
    tickets = client.get("/tickets").json()
    alice = next(t for t in tickets if t["customer_id"] == "CUST-100")
    assert alice["tags"] == ["login", "password"]


def test_csv_format_inferred_from_extension(client, fixtures_dir):
    content = (fixtures_dir / "valid.csv").read_bytes()
    r = import_bytes(client, "valid.csv", content)  # no explicit format
    assert r.status_code == 200
    assert r.json()["successful"] == 3


def test_import_format_cannot_be_determined(client):
    r = import_bytes(client, "file_without_extension", b"data")  # no format, no extension
    assert r.status_code == 400
    assert "error" in r.json()


def test_import_too_many_records_is_rejected(make_client, fixtures_dir):
    client = make_client(max_import_records=1)
    content = (fixtures_dir / "valid.csv").read_bytes()  # 3 rows
    r = import_bytes(client, "valid.csv", content, fmt="csv")
    assert r.status_code == 413
    assert "error" in r.json()


def test_import_file_too_large_is_rejected(make_client, fixtures_dir):
    client = make_client(max_import_bytes=10)
    content = (fixtures_dir / "valid.csv").read_bytes()
    r = import_bytes(client, "valid.csv", content, fmt="csv")
    assert r.status_code == 413
