# Self-Verification Report — Homework 2

**Quality gate (authoritative, `./demo/quality.sh`):**
`ruff` ✅ clean · `mypy` ✅ no issues (16 files) · `bandit` ✅ clean · `radon` ✅ avg A (2.30), **no C+ blocks** ·
**pytest ✅ 82 passed** · **coverage ✅ 98.41%** (gate `fail_under = 95`).
Verified live under `uvicorn` with real HTTP (create, auto-classify, multipart import, filter, 404, delete).

## Requirements traceability

| Requirement | Status | Evidence |
|---|---|---|
| 6 CRUD/import endpoints, correct verbs/paths/codes | ✅ | `src/routes/tickets.py` (`/import` declared before `/{id}`); live 201/200/204/400/404 |
| Ticket model: all spec fields + enums + bounds | ✅ | `src/models/ticket.py` (EmailStr; subject 1–200; description 10–2000; 5 enums) |
| CSV / JSON / XML parsing | ✅ | `src/services/parsers.py`; `test_import_{csv,json,xml}.py` |
| Validation of required fields/enums/lengths/email | ✅ | single Pydantic path for API + import; `test_ticket_model.py` |
| Bulk import summary (total/successful/failed + per-row errors) | ✅ | `src/models/views.py` `ImportSummary`/`RowError`; `import_service.py` |
| Malformed file → graceful 400 (no 500) | ✅ | `parsers.py` raises `ApiError(400)`; `test_import_*` malformed cases |
| Auto-classify: category, priority, confidence∈[0,1], reasoning, keywords_found | ✅ | `classifier.py` + `views.ClassificationResult`; `test_categorization.py` |
| Category rules (6) + priority keyword rules (urgent/high/med/low) | ✅ | `classifier.py:14-39` matches spec keywords exactly |
| Auto-run on create (flag), store confidence, manual override, log decisions | ✅ | `?auto_classify`; `ticket_service.py` (persists + logs); override via PUT |
| Test files & minimum counts | ✅ | api 13≥11, model 9(14 cases)≥9, csv 9≥6, json 5, xml 6, categorization 15 cases≥10, integration 5, performance 5 |
| Coverage > 85% | ✅ | **98.41%** measured |
| Docs: 5 files for different audiences, different models per type | ✅ | README + API_REFERENCE + ARCHITECTURE + TESTING_GUIDE + DEPLOYMENT; generated across Opus/Sonnet/Haiku (footers); 6 Mermaid; cURL per endpoint |
| Integration: lifecycle, bulk+classify, 20+ concurrency, combined filter | ✅ | `test_integration.py` (25 concurrent creates) |
| Performance benchmarks | ✅ | `test_performance.py` (asserted bounds) |
| Sample data 50/20/30 + invalid files | ✅ | `samples/` (counts verified); imports cleanly through the app |
| Shared error envelope + X-Request-ID + safe 500 | ✅ | `errors.py` + `main.py`; `test_quality.py` |

## Bugs found by adversarial review and fixed

| # | Severity | Issue | Fix | Regression test |
|---|---|---|---|---|
| 1 | High | Classifier used raw substring matching → "security" matched "insecurity", "error" matched "terror", "500" matched "1500" | Whole-token word-boundary regex (`classifier.py` `_compile`/`_matches`) | `test_keywords_do_not_match_inside_other_words` |
| 2 | Medium | Priority "urgent" list missing `"can not access"` (present in category list) | Added the variant | `test_can_not_access_spelling_is_urgent` |
| 3 | Medium | XML parser turned a single bare `<ticket>` doc into many empty rows | Detect `root.tag == "ticket"` → parse as one | `test_single_bare_ticket_without_wrapper` |
| 4 | Low | XML `findall("ticket") or list(root)` fallback fabricated bogus "failed" rows for a wrapper with non-`<ticket>` children | Removed the fallback; only real `<ticket>` children count | `test_xml_wrapper_without_ticket_children_imports_nothing` |

Lower-severity items reviewed and consciously deferred/documented: in-memory store has no cross-PUT locking (single-process homework — ASSUMPTIONS #13); "suggestion" is intentionally both a feature_request and low-priority signal (self-consistent).

## Assumptions
See `ASSUMPTIONS.md` (PUT = partial update; metadata source/device_type required, browser optional; defaults on create; auto-classify persists + overridable; coverage bar raised to 95%; whole-token matching; "5 docs" spec lists only 4; etc.).

## Known gaps / human-required steps
- None outstanding. `docs/screenshots/test_coverage.png` is now provided (rendered from the
  real coverage report); a `.txt` report and HTML report remain available too. The "5 docs"
  and "different models per doc type" requirements are satisfied (see ASSUMPTIONS #11–#12).
