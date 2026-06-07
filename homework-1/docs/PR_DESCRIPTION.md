# Homework 1 — Banking Transactions API (Python / FastAPI)

**Author:** Anton Tsiatsko · **Branch:** `atsiatsko_home_work_1` → `main` (this fork) · **Reviewer:** @Alexey-Popov

> ⚠️ Add screenshots to `homework-1/docs/screenshots/` and embed below before opening.

---

## Summary

In-memory banking transactions API, built TDD with Claude Code. **Tasks 1–3 + all four Task-4 features** (only one required). **53 tests pass · 99% coverage · static-analysis gate clean.**

## Scope

| Area | Delivered |
|------|-----------|
| Task 1 — Core API | CRUD + balance, 200/201/400/404, in-memory store |
| Task 2 — Validation | amount · currency-aware decimals · `ACC-XXXXX` · ISO-4217 · per-type rules → `{error, details[]}` |
| Task 3 — Filtering | `accountId` · `type` · date range · combinable |
| Task 4 — Extras | **A** summary · **B** interest · **C** CSV export · **D** rate-limit `429` |
| Beyond spec | one error envelope (incl. unknown route / 405) · safe 500s · `X-Request-ID` + logging · `/health` + `/docs` · `Decimal` money · multi-region seam · audit trail + PII masking |
| Quality gate | ruff · mypy · bandit · radon (avg A) · 99% coverage — `./demo/quality.sh`; `sonar-project.properties` for SonarQube |

## Verify

```bash
cd homework-1 && ./demo/run.sh    # http://localhost:3000  (docs at /docs)
pytest                            # 53 passed
./demo/quality.sh                 # ruff + mypy + bandit + radon + coverage (99%)
```

Details: [README](../README.md) · [HOWTORUN](../HOWTORUN.md) · requests in [`demo/sample-requests.http`](../demo/sample-requests.http).

## Notes for reviewer

- **One intentional deviation:** decimal precision is **currency-aware** (USD/EUR/GBP=2, JPY=0, BHD=3) rather than a hardcoded "max 2" — spec currencies still behave as ≤2.
- Architecture is layered (routers → validators/services → store); requirement→test traceability is in the README.

## AI tools

Claude Code: read docs → surfaced spec ambiguities → agreed design → TDD → reviewed every module.

## Screenshots
<!-- embed after adding to docs/screenshots/ -->
- [ ] Claude Code interaction · [ ] API running · [ ] sample request/response · [ ] `pytest` (28 passed)
