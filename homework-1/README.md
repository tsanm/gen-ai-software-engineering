# 🏦 Homework 1: Banking Transactions API

**Author:** Anton Tsiatsko · **Stack:** Python · FastAPI · Pydantic v2 · pytest · **AI:** Claude Code

In-memory REST API for banking transactions. **Tasks 1–3 done + all four Task-4 features.** 63 tests pass.

▶️ Run & test: [HOWTORUN.md](./HOWTORUN.md) · 📖 API docs: `/docs` (Swagger) · 📡 [live examples](./docs/API_EXAMPLES.md)

---

## What's covered

| Task | Status | Endpoints |
|------|--------|-----------|
| 1 — Core API | ✅ | `POST /transactions`, `GET /transactions`, `GET /transactions/{id}`, `GET /accounts/{id}/balance` |
| 2 — Validation | ✅ | amount, currency-aware decimals, `ACC-XXXXX`, ISO-4217, per-type rules → `{error, details[]}` |
| 3 — Filtering | ✅ | `?accountId` · `?type` · `?from`/`?to` · combinable |
| 4 — Extras (≥1 required) | ✅ **all 4** | A `/summary` · B `/interest` · C `/export?format=csv` · D rate-limit `429` |

**Beyond spec:** one error envelope (400/404/429/500), safe 500s, `X-Request-ID` + request logging, `/health`, `Decimal` money, multi-region seam, audit trail + PII masking.

---

## Architecture

Layered, dependencies pointing inward:
**routes** (thin HTTP adapters) → **services** (all business + domain logic: use-cases,
pure calculations, compliance, currency/region rules) → **models** (the data layer:
entities, response DTOs, and the store). Input checks live in **validators**; generic,
business-agnostic helpers in **utils**. Everything below `routes` is transport-agnostic,
so the same use-case could be driven by a queue consumer or CLI and return the same view
model.

```
src/
  main.py            app factory + middleware / exception handlers
  config.py          immutable settings (env-driven)
  errors.py          one error envelope for 400/404/429/500
  routes/            accounts.py · transactions.py · dependencies.py   (thin adapters + DI)
  services/          account_service.py · transaction_service.py       (use-cases)
                     calculations.py (balance/interest/filter/csv)
                     compliance.py · currencies.py · regions.py        (domain rules)
  models/            transaction.py (entity + create) · views.py (DTOs) · store.py
  validators/        transaction_validator.py · account_validator.py
  utils/             masking.py · rate_limit.py                        (generic helpers)
```

### Key decisions

| Decision | Choice |
|----------|--------|
| Money | `Decimal` end-to-end (no float drift) |
| Decimal precision | **Currency-aware** (USD=2, JPY=0, BHD=3) — supersedes literal "max 2"; spec currencies still ≤2 |
| Balance | derived from **completed** transactions only |
| Account format | `ACC-XXXXX`, behind a per-region strategy |
| Errors | one envelope `{error, details?, requestId}` for all failures |
| Config | immutable `Settings` injected → full test isolation |

### Extensibility (multi-region)

A `Region` (see `regions.py`) bundles currency rules, account format, allowed currencies, compliance policy, and an FX seam. **Onboarding a country = one config entry, no rewrites.**

**Out of scope** (seam exists, omitted for homework): DB · auth · real FX · IBAN · data residency · distributed rate limiting · CI/Docker.

---

## Code quality

Local static-analysis gate (the **SonarQube-equivalent** for Python) — one command: `./demo/quality.sh`.

| Tool | Checks | Status |
|------|--------|--------|
| ruff | lint, bugs, import order | ✅ clean |
| mypy | static type checking | ✅ no issues |
| bandit | security analysis | ✅ no issues |
| radon | cyclomatic complexity | ✅ avg **A**, no block above B |
| coverage | test coverage | ✅ **99%** (gate ≥95%) |

`sonar-project.properties` is included for SonarQube/SonarCloud if a server is available.

## Testing

63 tests, **API-level / domain-flow** (no brittle unit tests). Each spec requirement maps to a test:

| Requirement | Tests |
|-------------|-------|
| Task 1 (CRUD, 404, balance, positive amount) | `test_transactions.py` |
| Task 2 (all validation rules + error shape) | `test_validation.py` |
| Task 3 (filters + combined) | `test_filtering.py` |
| Task 4 (A/B/C/D) | `test_features.py` |
| Extras (envelope, 500-safety, request-id, precision, audit/PII) | `test_quality.py` |

---

## AI-assisted workflow (Claude Code)

Read docs → surfaced spec ambiguities → agreed design → **TDD** (tests first, then to green) → reviewed every module. Screenshots in [`docs/screenshots/`](./docs/screenshots/).
