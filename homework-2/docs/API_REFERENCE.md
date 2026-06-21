# API Reference — Intelligent Customer Support System

**Base URL:** `http://localhost:3000`
**Interactive docs:** `GET /docs` (Swagger UI) · `GET /openapi.json`
Every response carries an `X-Request-ID` header containing the UUID assigned to that request.

---

## Data Models

### Ticket

The full ticket object returned by every create, read, and update operation.

| Field | Type | Constraints / Notes |
|---|---|---|
| `id` | string (UUID) | Server-generated; never sent in a request body |
| `customer_id` | string | Non-empty |
| `customer_email` | string (email) | RFC-5322 validated |
| `customer_name` | string | Non-empty |
| `subject` | string | 1–200 characters |
| `description` | string | 10–2000 characters |
| `category` | enum | See values below; default `other` |
| `priority` | enum | See values below; default `medium` |
| `status` | enum | See values below; default `new` |
| `created_at` | string (ISO-8601 datetime) | Server-managed; set on creation |
| `updated_at` | string (ISO-8601 datetime) | Server-managed; updated on every write |
| `resolved_at` | string (ISO-8601 datetime) \| null | Set automatically when `status` becomes `resolved` or `closed`; cleared on reopen |
| `assigned_to` | string \| null | Agent identifier; optional |
| `tags` | string[] | Default `[]` |
| `metadata` | object | See sub-object below; required on creation |
| `classification_confidence` | number (0–1) \| null | Populated after auto-classify; null otherwise |

#### Enum values

| Field | Allowed values |
|---|---|
| `category` | `account_access` \| `technical_issue` \| `billing_question` \| `feature_request` \| `bug_report` \| `other` |
| `priority` | `urgent` \| `high` \| `medium` \| `low` |
| `status` | `new` \| `in_progress` \| `waiting_customer` \| `resolved` \| `closed` |

#### `metadata` sub-object

| Field | Type | Allowed values / Notes |
|---|---|---|
| `source` | enum | `web_form` \| `email` \| `api` \| `chat` \| `phone` — **required** |
| `device_type` | enum | `desktop` \| `mobile` \| `tablet` — **required** |
| `browser` | string \| null | Optional free-text; e.g. `"Chrome 124"` |

---

### ImportSummary

Returned by `POST /tickets/import`.

| Field | Type | Notes |
|---|---|---|
| `total` | integer | Total rows parsed from the file |
| `successful` | integer | Rows that were saved as tickets |
| `failed` | integer | Rows that failed validation |
| `created_ids` | string[] | IDs of all successfully created tickets |
| `errors` | RowError[] | One entry per failed row |

**RowError:**

| Field | Type | Notes |
|---|---|---|
| `row` | integer | Zero-based row index in the source file |
| `errors` | object[] | `[{"field": "...", "message": "..."}]` |

---

### ClassificationResult

Returned by `POST /tickets/{id}/auto-classify`.

| Field | Type | Notes |
|---|---|---|
| `category` | enum | Predicted category (same values as `Ticket.category`) |
| `priority` | enum | Predicted priority (same values as `Ticket.priority`) |
| `confidence` | number (0–1) | Model confidence score |
| `reasoning` | string | Human-readable explanation of the classification decision |
| `keywords_found` | string[] | Signal words that drove the classification |

---

### Error Envelope

Every error response (4xx and 5xx) uses the same JSON shape:

```json
{
  "error": "Validation failed",
  "details": [
    { "field": "customer_email", "message": "value is not a valid email address" }
  ],
  "requestId": "f1c2d3e4-..."
}
```

| Field | Type | Notes |
|---|---|---|
| `error` | string | Short human-readable summary |
| `details` | object[] \| absent | Present only when per-field information is available; each item has `field` (string \| null) and `message` (string) |
| `requestId` | string \| absent | Echoes the `X-Request-ID` assigned to the request |

---

### Status Code Table

| Code | Meaning |
|---|---|
| `201` | Resource created successfully |
| `200` | Request successful |
| `204` | Deleted — no response body |
| `400` | Validation failure, malformed import file, or unrecognised `format` value |
| `404` | Ticket not found |
| `413` | Import file exceeds the byte limit, or import record count exceeds the record limit |
| `500` | Unexpected server error (generic message; no stack trace in body) |

---

## Endpoints

### POST /tickets

Create a single support ticket.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `auto_classify` | boolean | `false` | If `true`, run keyword-based auto-classification immediately after creation and persist the results on the ticket |

**Request body** — `application/json`

All `TicketCreate` fields; `category`, `priority`, `status`, and `tags` are optional (see defaults above). `metadata` is required.

```json
{
  "customer_id": "CUST-001",
  "customer_email": "jane@example.com",
  "customer_name": "Jane Doe",
  "subject": "Cannot log in after password reset",
  "description": "Since the password reset yesterday I cannot access my account. The page shows an error on submit.",
  "category": "account_access",
  "priority": "high",
  "status": "new",
  "assigned_to": null,
  "tags": ["login", "urgent"],
  "metadata": {
    "source": "web_form",
    "browser": "Chrome 124",
    "device_type": "desktop"
  }
}
```

**Response — 201 Created**

```json
{
  "id": "3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c",
  "customer_id": "CUST-001",
  "customer_email": "jane@example.com",
  "customer_name": "Jane Doe",
  "subject": "Cannot log in after password reset",
  "description": "Since the password reset yesterday I cannot access my account. The page shows an error on submit.",
  "category": "account_access",
  "priority": "high",
  "status": "new",
  "created_at": "2024-06-08T10:23:45.123456",
  "updated_at": "2024-06-08T10:23:45.123456",
  "resolved_at": null,
  "assigned_to": null,
  "tags": ["login", "urgent"],
  "metadata": {
    "source": "web_form",
    "browser": "Chrome 124",
    "device_type": "desktop"
  },
  "classification_confidence": null
}
```

**Error responses:** `400` if the body fails validation.

**cURL example**

```bash
curl -s -X POST 'http://localhost:3000/tickets?auto_classify=false' \
  -H 'Content-Type: application/json' \
  -d '{
    "customer_id": "CUST-001",
    "customer_email": "jane@example.com",
    "customer_name": "Jane Doe",
    "subject": "Cannot log in after password reset",
    "description": "Since the password reset yesterday I cannot access my account. The page shows an error on submit.",
    "category": "account_access",
    "priority": "high",
    "status": "new",
    "tags": ["login", "urgent"],
    "metadata": {
      "source": "web_form",
      "browser": "Chrome 124",
      "device_type": "desktop"
    }
  }'
```

---

### POST /tickets/import

Bulk-import tickets from a CSV, JSON, or XML file. One invalid row never aborts the whole import; it is recorded in `errors` and processing continues.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `format` | `csv` \| `json` \| `xml` \| absent | Inferred from file extension | Override the file format. Required when the uploaded filename has no recognised extension. |
| `auto_classify` | boolean | `false` | Run auto-classification on every successfully parsed ticket |

**Request body** — `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | file | The import file — **required** |

**Accepted file formats**

- **CSV** — header row required; column names must match `TicketCreate` field names; nested `metadata.*` fields use dot notation (e.g. `metadata.source`).
- **JSON** — top-level array of objects, each matching the `TicketCreate` shape.
- **XML** — root element wrapping `<ticket>` child elements whose child tags are field names.

**Response — 200 OK**

```json
{
  "total": 3,
  "successful": 2,
  "failed": 1,
  "created_ids": [
    "3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c",
    "7a9b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
  ],
  "errors": [
    {
      "row": 2,
      "errors": [
        { "field": "customer_email", "message": "value is not a valid email address" }
      ]
    }
  ]
}
```

**Error responses**

| Code | When |
|---|---|
| `400` | File content is malformed (unparseable CSV/JSON/XML) or `format` value is not `csv`, `json`, or `xml`, or no format can be inferred from the filename |
| `413` | File size exceeds the server byte limit (default 5 MB), or the number of parsed records exceeds the server record limit (default 1 000) |

**cURL examples**

```bash
# CSV upload with explicit format and auto-classify
curl -s -X POST 'http://localhost:3000/tickets/import?format=csv&auto_classify=true' \
  -F 'file=@/path/to/tickets.csv'

# JSON upload — format inferred from filename
curl -s -X POST 'http://localhost:3000/tickets/import' \
  -F 'file=@/path/to/tickets.json'

# XML upload with explicit format
curl -s -X POST 'http://localhost:3000/tickets/import?format=xml' \
  -F 'file=@/path/to/tickets.xml'
```

---

### GET /tickets

List tickets, with optional filtering. All parameters are optional and combinable.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `category` | enum | Filter by category (`account_access` \| `technical_issue` \| `billing_question` \| `feature_request` \| `bug_report` \| `other`) |
| `priority` | enum | Filter by priority (`urgent` \| `high` \| `medium` \| `low`) |
| `status` | enum | Filter by status (`new` \| `in_progress` \| `waiting_customer` \| `resolved` \| `closed`) |
| `assigned_to` | string | Filter by agent identifier (exact match) |

**Response — 200 OK**

Returns a JSON array of `Ticket` objects (may be empty).

```json
[
  {
    "id": "3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c",
    "customer_id": "CUST-001",
    "customer_email": "jane@example.com",
    "customer_name": "Jane Doe",
    "subject": "Cannot log in after password reset",
    "description": "Since the password reset yesterday I cannot access my account. The page shows an error on submit.",
    "category": "account_access",
    "priority": "high",
    "status": "new",
    "created_at": "2024-06-08T10:23:45.123456",
    "updated_at": "2024-06-08T10:23:45.123456",
    "resolved_at": null,
    "assigned_to": null,
    "tags": ["login", "urgent"],
    "metadata": {
      "source": "web_form",
      "browser": "Chrome 124",
      "device_type": "desktop"
    },
    "classification_confidence": null
  }
]
```

**Error responses:** `400` if a query parameter value is not a valid enum member.

**cURL examples**

```bash
# All tickets
curl -s 'http://localhost:3000/tickets'

# Filter by category and priority
curl -s 'http://localhost:3000/tickets?category=billing_question&priority=high'

# Filter by status and assigned agent
curl -s 'http://localhost:3000/tickets?status=in_progress&assigned_to=agent-7'

# Combine all four filters
curl -s 'http://localhost:3000/tickets?category=technical_issue&priority=urgent&status=new&assigned_to=agent-3'
```

---

### GET /tickets/{id}

Fetch a single ticket by its ID.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Ticket UUID |

**Response — 200 OK** — the `Ticket` object (see shape above).

**Error responses:** `404` if no ticket with the given ID exists.

**cURL example**

```bash
curl -s 'http://localhost:3000/tickets/3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c'
```

---

### PUT /tickets/{id}

Partially update a ticket. Only the fields present in the request body are changed; omitted fields retain their current values. `updated_at` is always refreshed. Moving `status` to `resolved` or `closed` sets `resolved_at`; changing it back to any other status clears `resolved_at`.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Ticket UUID |

**Request body** — `application/json`

All fields are optional. Provide only the fields you want to change.

```json
{
  "status": "resolved",
  "assigned_to": "agent-7",
  "priority": "medium"
}
```

Any subset of `TicketUpdate` fields is valid:

```json
{
  "customer_id": "CUST-001",
  "customer_email": "jane@example.com",
  "customer_name": "Jane Doe",
  "subject": "Updated subject",
  "description": "Updated description with enough characters.",
  "category": "technical_issue",
  "priority": "urgent",
  "status": "in_progress",
  "assigned_to": "agent-5",
  "tags": ["login", "escalated"],
  "metadata": {
    "source": "email",
    "browser": null,
    "device_type": "mobile"
  }
}
```

**Response — 200 OK** — the full updated `Ticket` object.

**Error responses:** `400` if any provided field fails validation; `404` if the ticket does not exist.

**cURL examples**

```bash
# Change status and assignee
curl -s -X PUT 'http://localhost:3000/tickets/3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c' \
  -H 'Content-Type: application/json' \
  -d '{"status": "resolved", "assigned_to": "agent-7"}'

# Escalate priority
curl -s -X PUT 'http://localhost:3000/tickets/3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c' \
  -H 'Content-Type: application/json' \
  -d '{"priority": "urgent"}'
```

---

### DELETE /tickets/{id}

Permanently delete a ticket.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Ticket UUID |

**Response — 204 No Content** — empty body.

**Error responses:** `404` if no ticket with the given ID exists.

**cURL example**

```bash
curl -s -X DELETE 'http://localhost:3000/tickets/3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c' \
  -o /dev/null -w '%{http_code}\n'
# Prints: 204
```

---

### POST /tickets/{id}/auto-classify

Run keyword-based classification on an existing ticket's subject and description. The ticket's `category`, `priority`, and `classification_confidence` fields are updated in place; existing values are overwritten. A user may still manually override the result via `PUT /tickets/{id}`.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Ticket UUID |

**Request body** — none.

**Response — 200 OK** — a `ClassificationResult` object:

```json
{
  "category": "technical_issue",
  "priority": "urgent",
  "confidence": 0.93,
  "reasoning": "Category 'technical_issue' from signals: 'error', 'crash'. Priority 'urgent' from keywords: 'production down'.",
  "keywords_found": ["error", "crash", "production down"]
}
```

**Error responses:** `404` if no ticket with the given ID exists.

**cURL example**

```bash
curl -s -X POST 'http://localhost:3000/tickets/3f6e8a1c-0b2d-4e5f-9a7c-1d2e3f4a5b6c/auto-classify'
```

---

### GET /health

Liveness probe. Returns immediately without touching persistent state.

**Response — 200 OK**

```json
{ "status": "ok" }
```

**cURL example**

```bash
curl -s 'http://localhost:3000/health'
```

---

## Ops Endpoints (informational)

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe — `{"status":"ok"}` |
| `GET` | `/` | Service metadata — `{"name": "...", "docs": "/docs", "health": "/health"}` |
| `GET` | `/docs` | Swagger UI (interactive) |
| `GET` | `/openapi.json` | Raw OpenAPI schema |

---

*Generated with Claude Sonnet 4.6 — API reference (mechanical extraction of endpoint contracts).*
