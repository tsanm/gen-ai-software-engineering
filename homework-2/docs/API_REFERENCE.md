# API Reference — Intelligent Customer Support System

Base URL (local): `http://localhost:3000`. All responses carry an `X-Request-ID` header.
Interactive docs: `GET /docs` (Swagger UI), `GET /openapi.json`.

## Data models

### Ticket (response)

| Field | Type | Notes |
|---|---|---|
| `id` | string (UUID) | server-generated |
| `customer_id` | string | non-empty |
| `customer_email` | string (email) | RFC-validated |
| `customer_name` | string | non-empty |
| `subject` | string | 1–200 chars |
| `description` | string | 10–2000 chars |
| `category` | enum | `account_access` \| `technical_issue` \| `billing_question` \| `feature_request` \| `bug_report` \| `other` |
| `priority` | enum | `urgent` \| `high` \| `medium` \| `low` |
| `status` | enum | `new` \| `in_progress` \| `waiting_customer` \| `resolved` \| `closed` |
| `created_at` / `updated_at` | datetime (ISO-8601) | server-managed |
| `resolved_at` | datetime \| null | set when status becomes `resolved`/`closed` |
| `assigned_to` | string \| null | |
| `tags` | string[] | |
| `metadata` | object | `{ source, browser?, device_type }` |
| `classification_confidence` | number \| null | set after auto-classify |

`metadata.source` ∈ `web_form｜email｜api｜chat｜phone`; `metadata.device_type` ∈ `desktop｜mobile｜tablet`.

### Error envelope (every failure)

```json
{ "error": "Validation failed",
  "details": [{ "field": "customer_email", "message": "value is not a valid email address" }],
  "requestId": "f1c2…" }
```

| Status | Meaning |
|---|---|
| 201 | Created |
| 200 | OK |
| 204 | Deleted (no body) |
| 400 | Validation / malformed import file / bad format |
| 404 | Ticket not found |
| 413 | Import file or record count over limit |
| 500 | Unexpected error (generic body, no traceback) |

---

## Endpoints

### `POST /tickets` — create a ticket
Query: `auto_classify` (bool, default `false`).

```bash
curl -s -X POST http://localhost:3000/tickets \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"CUST-1","customer_email":"jane@example.com","customer_name":"Jane",
       "subject":"Cannot log in","description":"I cannot access my account after the update.",
       "metadata":{"source":"web_form","browser":"Chrome","device_type":"desktop"}}'
```
→ `201` with the created Ticket.

### `POST /tickets/import` — bulk import (CSV/JSON/XML)
Multipart form upload. Query: `format` (`csv｜json｜xml`, else inferred from filename),
`auto_classify` (bool).

```bash
curl -s -X POST 'http://localhost:3000/tickets/import?format=csv&auto_classify=true' \
  -F 'file=@samples/sample_tickets.csv'
```
→ `200` with an import summary:
```json
{ "total": 50, "successful": 50, "failed": 0,
  "created_ids": ["…"], "errors": [] }
```
A failed row appears as `{"row": <index>, "errors": [{"field": "...", "message": "..."}]}`.
A malformed file returns `400`; a file/row count over the limit returns `413`.

### `GET /tickets` — list with filtering
Query (all optional, combinable): `category`, `priority`, `status`, `assigned_to`.

```bash
curl -s 'http://localhost:3000/tickets?category=billing_question&priority=high'
```
→ `200` with a JSON array of Tickets.

### `GET /tickets/{id}` — fetch one
```bash
curl -s http://localhost:3000/tickets/<id>
```
→ `200` with the Ticket, or `404`.

### `PUT /tickets/{id}` — partial update
Only the provided fields change; `updated_at` is bumped; moving to `resolved`/`closed`
stamps `resolved_at` (reopening clears it).

```bash
curl -s -X PUT http://localhost:3000/tickets/<id> \
  -H 'Content-Type: application/json' \
  -d '{"status":"resolved","assigned_to":"agent-7"}'
```
→ `200` with the updated Ticket, or `404`.

### `DELETE /tickets/{id}` — delete
```bash
curl -s -X DELETE http://localhost:3000/tickets/<id> -o /dev/null -w '%{http_code}\n'
```
→ `204` (no body), or `404`.

### `POST /tickets/{id}/auto-classify` — classify category & priority
```bash
curl -s -X POST http://localhost:3000/tickets/<id>/auto-classify
```
→ `200`:
```json
{ "category": "technical_issue", "priority": "urgent", "confidence": 0.93,
  "reasoning": "Category 'technical_issue' from signals: 'error', 'crash'. Priority 'urgent' from keywords: 'production down'.",
  "keywords_found": ["error", "crash", "production down"] }
```
The result is persisted on the ticket (`category`, `priority`, `classification_confidence`);
a user may still override via `PUT`. Returns `404` if the ticket does not exist.

### Ops
- `GET /health` → `{"status":"ok"}`
- `GET /` → service metadata

---

*Generated with Claude Sonnet 4.6 — chosen for fast, mechanical extraction of endpoint
request/response shapes from the route definitions.*
