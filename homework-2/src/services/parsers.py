"""Import file parsers for CSV, JSON, and XML (Task 1).

Each parser turns raw file bytes into a list of canonical row dicts (nested ``metadata``,
``tags`` as a list) that can be fed straight into ``TicketCreate``. Parsing concerns
(decoding, structure) are separated from validation concerns (field rules); a malformed
file raises ``ApiError(400)`` so the caller never sees a 500.

XML is parsed with ``defusedxml`` to prevent XXE / entity-expansion attacks.
"""
from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable

from defusedxml import ElementTree as DefusedET

from src.errors import ApiError

SUPPORTED_FORMATS = ("csv", "json", "xml")
_META_FIELDS = {"source", "browser", "device_type"}


def _bad(fmt: str, message: str) -> ApiError:
    return ApiError(400, f"Malformed {fmt} file", [{"field": None, "message": message}])


def _decode(content: bytes, fmt: str) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _bad(fmt, "File is not valid UTF-8 text") from exc


def _split_tags(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _row_from_flat(flat: dict) -> dict:
    """Build a canonical (nested) row from a flat key/value mapping.

    Empty values are dropped so Pydantic defaults apply; ``source``/``browser``/
    ``device_type`` are folded into a nested ``metadata`` object.
    """
    row: dict = {}
    meta: dict = {}
    for key, value in flat.items():
        if key is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if value is None or value == "":
            continue
        if key in _META_FIELDS:
            meta[key] = value
        elif key == "tags":
            row["tags"] = _split_tags(value)
        else:
            row[key] = value
    if meta:
        row["metadata"] = meta
    return row


def parse_csv(content: bytes) -> list[dict]:
    reader = csv.DictReader(io.StringIO(_decode(content, "csv")))
    if reader.fieldnames is None:
        return []
    return [_row_from_flat(raw) for raw in reader]


def parse_json(content: bytes) -> list[dict]:
    try:
        data = json.loads(_decode(content, "json"))
    except json.JSONDecodeError as exc:
        raise _bad("json", f"Invalid JSON: {exc.msg}") from exc

    if isinstance(data, dict):
        data = data.get("tickets", data.get("data"))
    if not isinstance(data, list):
        raise _bad("json", "Expected a JSON array of ticket objects")

    rows: list[dict] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise _bad("json", f"Record {index} is not a JSON object")
        rows.append(_canonical_json_row(item))
    return rows


def _canonical_json_row(item: dict) -> dict:
    if isinstance(item.get("metadata"), dict):
        row = dict(item)
        if "tags" in row:
            row["tags"] = _split_tags(row["tags"])
        return row
    return _row_from_flat(item)


def parse_xml(content: bytes) -> list[dict]:
    try:
        root = DefusedET.fromstring(content)
    except Exception as exc:  # defusedxml raises various ParseError/EntitiesForbidden
        raise _bad("xml", f"Invalid XML: {exc}") from exc

    if root.tag == "ticket":            # a single bare <ticket> document
        nodes = [root]
    else:                               # a <tickets> wrapper: only real <ticket> children count
        nodes = root.findall("ticket")
    return [_row_from_xml(node) for node in nodes]


def _xml_metadata(node) -> dict:
    return {m.tag: (m.text or "").strip() for m in node if (m.text or "").strip()}


def _xml_tags(node) -> list[str]:
    return [(t.text or "").strip() for t in node if (t.text or "").strip()]


def _row_from_xml(node) -> dict:
    flat: dict = {}
    nested: dict = {}
    for child in node:
        if child.tag == "metadata":
            nested["metadata"] = _xml_metadata(child)
        elif child.tag == "tags":
            nested["tags"] = _xml_tags(child)
        else:
            flat[child.tag] = child.text
    row = _row_from_flat(flat)
    row.update(nested)  # explicit nested metadata/tags override flat-derived values
    return row


_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    "csv": parse_csv,
    "json": parse_json,
    "xml": parse_xml,
}


def parse_records(content: bytes, fmt: str) -> list[dict]:
    """Dispatch to the parser for ``fmt`` and return canonical row dicts."""
    parser = _PARSERS.get(fmt.lower())
    if parser is None:
        raise ApiError(400, "Unsupported import format", [
            {"field": "format",
             "message": f"Supported formats are: {', '.join(SUPPORTED_FORMATS)}"}])
    return parser(content)
