"""Task 3 — XML import parsing tests (5 tests), including an XXE security test."""
from conftest import import_bytes


def test_valid_xml_imports_all_rows(client, fixtures_dir):
    content = (fixtures_dir / "valid.xml").read_bytes()
    r = import_bytes(client, "valid.xml", content, fmt="xml")
    assert r.status_code == 200
    assert r.json()["successful"] == 2


def test_malformed_xml_is_rejected_gracefully(client):
    r = import_bytes(client, "bad.xml", b"<tickets><ticket></broken>", fmt="xml")
    assert r.status_code == 400
    assert "error" in r.json()


def test_xxe_external_entity_is_blocked(client, fixtures_dir):
    """defusedxml must refuse the external-entity payload (no file disclosure, no 500)."""
    content = (fixtures_dir / "xxe.xml").read_bytes()
    r = import_bytes(client, "xxe.xml", content, fmt="xml")
    assert r.status_code == 400
    assert "root:" not in r.text  # /etc/passwd never expanded into the response


def test_xml_nested_tags_are_parsed(client, fixtures_dir):
    content = (fixtures_dir / "valid.xml").read_bytes()
    import_bytes(client, "valid.xml", content, fmt="xml")
    tickets = client.get("/tickets").json()
    frank = next(t for t in tickets if t["customer_id"] == "CUST-400")
    assert set(frank["tags"]) == {"outage", "critical"}
    assert frank["metadata"]["source"] == "phone"


def test_single_bare_ticket_without_wrapper(client):
    """A lone <ticket> document (no <tickets> wrapper) imports as exactly one ticket."""
    xml = (b"<ticket>"
           b"<customer_id>C1</customer_id>"
           b"<customer_email>solo@example.com</customer_email>"
           b"<customer_name>Solo</customer_name>"
           b"<subject>Single ticket file</subject>"
           b"<description>This is a single bare ticket document without a wrapper.</description>"
           b"<metadata><source>api</source><device_type>desktop</device_type></metadata>"
           b"</ticket>")
    r = import_bytes(client, "single.xml", xml, fmt="xml")
    summary = r.json()
    assert summary["total"] == 1
    assert summary["successful"] == 1
    assert summary["failed"] == 0


def test_xml_wrapper_without_ticket_children_imports_nothing(client):
    """A wrapper whose children are not <ticket> yields zero records (not bogus failures)."""
    r = import_bytes(client, "weird.xml", b"<tickets><foo>x</foo><bar>y</bar></tickets>", fmt="xml")
    assert r.status_code == 200
    assert r.json()["total"] == 0
    assert r.json()["failed"] == 0


def test_xml_invalid_row_is_counted_as_failed(client):
    xml = (b"<tickets><ticket>"
           b"<customer_id>C1</customer_id>"
           b"<customer_email>bad-email</customer_email>"
           b"<customer_name>Bad</customer_name>"
           b"<subject>Subject here</subject>"
           b"<description>A sufficiently long description string.</description>"
           b"<metadata><source>api</source><device_type>desktop</device_type></metadata>"
           b"</ticket></tickets>")
    r = import_bytes(client, "bad_row.xml", xml, fmt="xml")
    summary = r.json()
    assert summary["total"] == 1
    assert summary["failed"] == 1
