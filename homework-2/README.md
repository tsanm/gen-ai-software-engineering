# Intelligent Customer Support API

> An in-memory customer-support ticket system with multi-format bulk import and rule-based auto-classification.
>
> **Author:** Anton Tsiatsko

---

## Features

- **Ticket CRUD** — create, read, update, and delete support tickets, with list filtering by `category`, `priority`, `status`, and `assigned_to`.
- **Multi-format bulk import** — `POST /tickets/import` ingests CSV, JSON, or XML (format inferred from the file extension or forced with `?format=`). Each record is validated independently, so one bad row never aborts the batch; the response is a per-batch summary of `total` / `successful` / `failed`, the `created_ids`, and a structured error list keyed by row.
- **Rule-based auto-classification** — `POST /tickets/{id}/auto-classify` derives `category` and `priority` from ticket text and returns a `confidence` score, human-readable `reasoning`, and the matched `keywords_found`. Available as an opt-in flag (`?auto_classify=true`) on both create and import.
- **One error envelope** — every failure (400/404/422/500) renders as a single `{error, details[], requestId}` shape; client tracebacks are never leaked.
- **Request tracing** — every response carries an `X-Request-ID` header (also echoed in the error envelope's `requestId`).
- **Safe XML parsing** — imports use `defusedxml`, blocking XXE and entity-expansion attacks.
- **Operational endpoints** — `GET /health` and interactive Swagger UI at `/docs`.
- **Injectable configuration** — immutable `Settings` (import size/record caps, log level) built per app via `create_app()`, giving each test fully isolated state with no module-level globals.

## Architecture

The system is a strict layered design: dependencies point inward (**routes → services → models/store**). Routes are thin HTTP adapters; all domain logic, validation, and classification live in the services and Pydantic models. Cross-cutting concerns (request-id middleware, the single error envelope) wrap the request lifecycle.

```mermaid
flowchart TD
    Client([Client])
    Client -->|HTTP request| MW[Middleware<br/>request-id + access logging]
    MW --> Routes[routes/tickets.py<br/>thin HTTP adapters]

    Routes --> TS[services/TicketService]
    Routes --> IS[services/ImportService]

    IS --> P[services/parsers.py<br/>CSV / JSON / XML]
    IS --> TS
    TS --> CL[services/classifier.py<br/>rule-based engine]
    TS --> Store[(models/TicketStore<br/>in-memory dict)]

    Models[models/ticket.py + views.py<br/>Pydantic v2 entities & DTOs]
    TS -.validates with.-> Models
    Routes -.serializes with.-> Models

    Routes -. raises ApiError .-> EH[errors.py + exception handlers]
    TS -. raises ApiError .-> EH
    IS -. raises ApiError .-> EH
    EH ==> Env{{One error envelope<br/>error, details[], requestId}}
    Env -->|X-Request-ID| Client
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for component-level detail and data-flow diagrams.

## Installation & setup

Requires **Python 3.10+**. Run all commands from the `homework-2/` directory.

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements-dev.txt   # runtime + tooling
./demo/run.sh                                               # starts the API
```

The API listens on **http://localhost:3000**, with interactive Swagger docs at **http://localhost:3000/docs**.

Ready-made datasets live in [`samples/`](samples) (50-row CSV, 20-object JSON, 30-record XML, plus matching invalid files); copy-paste requests are in [`demo/sample-requests.http`](demo/sample-requests.http).

### Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/tickets` | Create a ticket (`?auto_classify=true` optional) |
| `POST` | `/tickets/import` | Bulk import from CSV / JSON / XML |
| `GET` | `/tickets` | List tickets, filterable by `category`/`priority`/`status`/`assigned_to` |
| `GET` | `/tickets/{id}` | Fetch a single ticket |
| `PUT` | `/tickets/{id}` | Update a ticket |
| `DELETE` | `/tickets/{id}` | Delete a ticket |
| `POST` | `/tickets/{id}/auto-classify` | Classify category + priority from ticket text |
| `GET` | `/health` | Liveness probe |

Full request/response reference: [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md).

## Running tests

```bash
./.venv/bin/python -m pytest --cov=src --cov-report=term-missing   # 82 tests, ~98% coverage
./demo/quality.sh                                                  # full quality gate
```

`./demo/quality.sh` runs the complete local gate: **ruff** (lint + import order), **mypy** (static types), **bandit** (security analysis), **radon** (cyclomatic complexity — fails on any C-or-worse block), and **pytest + coverage** (fails under 95%).

See [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) for the test pyramid, fixtures, and a manual testing checklist.

## Project structure

```
homework-2/
├── src/
│   ├── main.py                 # app factory, request-id middleware, exception handlers
│   ├── config.py               # immutable Settings (injected per app)
│   ├── errors.py               # ApiError + the single error envelope
│   ├── models/
│   │   ├── ticket.py           # Pydantic entities, enums, create/update payloads
│   │   ├── views.py            # ImportSummary, ClassificationResult, RowError DTOs
│   │   └── store.py            # in-memory ticket store
│   ├── routes/
│   │   ├── tickets.py          # thin HTTP adapters for /tickets
│   │   └── dependencies.py     # FastAPI dependency providers (from app.state)
│   └── services/
│       ├── ticket_service.py   # ticket use-cases (CRUD, filtering, classify)
│       ├── import_service.py   # bulk-import orchestration + caps
│       ├── parsers.py          # CSV / JSON / XML parsing (defusedxml)
│       └── classifier.py       # rule-based category/priority engine
├── tests/                      # 9 test files + fixtures/  (pytest)
├── docs/                       # API_REFERENCE, ARCHITECTURE, TESTING_GUIDE, DEPLOYMENT, screenshots/
├── samples/                    # deliverable datasets (valid + invalid CSV/JSON/XML)
├── demo/                       # run.sh, quality.sh, sample-requests.http
├── requirements.txt            # runtime dependencies
├── requirements-dev.txt        # runtime + tooling
└── pyproject.toml              # ruff / mypy / bandit / pytest / coverage config
```

## Further documentation

- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) — endpoint-by-endpoint request/response reference.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layered design, components, and data-flow diagrams.
- [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) — test pyramid, fixtures, and manual checklist.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — running and deploying the service.
- [`ASSUMPTIONS.md`](ASSUMPTIONS.md) — design decisions and scope assumptions.

## AI usage

This homework was built AI-first with Claude Code (Opus 4.8) using the **Context → Model → Prompt**
method. Screenshots of the interactions are in [`docs/screenshots/`](docs/screenshots/):

| Step | Screenshot | What it shows |
|------|-----------|---------------|
| Context | [`ai_usage_1_context.png`](docs/screenshots/ai_usage_1_context.png) | Gathering context — reading the workshop deck and `TASKS.md` to capture the real requirements. |
| Model + Prompt | [`ai_usage_2_build_prompt.png`](docs/screenshots/ai_usage_2_build_prompt.png) | Authoring the reusable, self-contained build prompt (`BUILD_PROMPT.md`). |
| Execution | [`ai_usage_3_execution.png`](docs/screenshots/ai_usage_3_execution.png) | Executing the prompt end-to-end — scaffolding the project mirroring homework-1's conventions. |

Test-coverage evidence: [`test_coverage.png`](docs/screenshots/test_coverage.png) · [`coverage_report.txt`](docs/screenshots/coverage_report.txt).

---

*Generated with Claude Opus 4.8 — developer documentation (structural overview of the codebase).*
