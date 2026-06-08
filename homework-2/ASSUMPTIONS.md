# Assumptions & Resolutions

Where `TASKS.md` left a detail unspecified, the choice made and the reasoning:

1. **PUT is a partial update.** The spec lists "Update ticket" without semantics. `PUT
   /tickets/{id}` applies only the fields present in the body (rather than requiring a full
   replacement), which is the more useful and forgiving behavior for a support tool.

2. **`customer_id` and `customer_name` must be non-empty.** The spec types them as "string"
   without bounds; empty values are rejected as they carry no meaning for a support ticket.

3. **`metadata.source` and `metadata.device_type` are required; `metadata.browser` is
   optional.** The model shows all three, but a browser is meaningless for phone/email
   sources, so it is nullable while the two enums are required.

4. **Defaults on create.** When not supplied, `category` defaults to `other`, `priority` to
   `medium`, and `status` to `new` — so a minimal create payload is valid and classification
   can fill the rest.

5. **Auto-classify persists its result.** The endpoint updates the ticket's `category`,
   `priority`, and `classification_confidence` (and logs the decision). "Manual override" is
   satisfied because a user can still `PUT` different values afterward.

6. **Category tie-breaking.** When text matches several categories equally, an explicit order
   decides the winner (e.g. a reproducible *defect* → `bug_report` over generic
   `technical_issue`). With no signals at all, the category is `other` at low confidence.

7. **Confidence formula.** Confidence is the average of a category score (rising with the
   number of matched keywords) and a priority score (high when a priority keyword matched).
   It is deterministic and always within `[0, 1]`; the exact value is illustrative, not a
   calibrated probability.

8. **Import is file-upload (multipart).** `POST /tickets/import` accepts an uploaded file;
   the format is taken from `?format=` or inferred from the filename extension.

9. **Import safety limits.** A file over `max_import_bytes` (5 MB) or a batch over
   `max_import_records` (1000) returns `413`. These guard against resource exhaustion and are
   configurable via `Settings`/environment.

10. **Coverage bar raised to 95%.** `TASKS.md` requires > 85%; homework-1 holds a 95% gate,
    so this project matches that higher bar (current ≈ 98%).

11. **Coverage screenshot.** `docs/screenshots/test_coverage.png` must be captured by a human
    from the terminal/HTML report (an automated agent cannot take a screenshot). See the
    self-verification report's "human-required steps". A text report is provided at
    `docs/screenshots/coverage_report.txt` and an HTML report via `pytest --cov-report=html`.

12. **"5 documentation files".** `TASKS.md` says "Generate 5 documentation files" but its own
    numbered list enumerates only four (README, API_REFERENCE, ARCHITECTURE, TESTING_GUIDE).
    All four named files are delivered; no fifth file is defined by the spec.

13. **Concurrency model.** The store is a single-process in-memory dict. Concurrent creates
    are safe (unique UUID keys; the 25-thread test passes), and reads are consistent. A
    multi-process or true-parallel deployment would require external storage with locking —
    out of scope for this in-memory homework. The `TicketStore` interface is the seam for that.

14. **Keyword matching is whole-token.** Classification matches keywords on word boundaries so
    a signal never fires inside an unrelated word (e.g. "security" does not match "insecurity",
    "500" does not match "1500"). This trades a little recall on creative spellings for
    precision, which is the right call for an explainable rules engine.
