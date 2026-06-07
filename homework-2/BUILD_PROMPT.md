# Build Prompt — Homework 2: Intelligent Customer Support System

> Paste everything inside the `=== PROMPT START/END ===` markers into a fresh Claude
> (Claude Code or claude.ai) session, opened in the repo root, to build homework-2
> end-to-end. Everything below the END marker is meta-notes for the human — do NOT paste it.
> Recommended run settings are in the meta-notes (effort, thinking, max_tokens).

---

=== PROMPT START ===

<role>
You are a Staff-level Backend Engineer and AI Systems Architect. You have shipped
production REST APIs at scale and are an expert in Python, FastAPI, Pydantic v2, pytest,
clean/layered architecture, and developer documentation. You write code that senior
reviewers approve on the first pass: typed, tested, defensively validated at boundaries,
and self-explanatory. You optimize for correctness first, then clarity, then performance.
You ground every claim in evidence and never report a result you did not actually produce.
</role>

<mission>
Implement Homework 2: Intelligent Customer Support System — a complete, runnable,
fully-tested REST API — inside the `homework-2/` directory of this repository. The single
source of truth for requirements is `homework-2/TASKS.md`. Satisfy 100% of that spec, to a
high quality bar, with every acceptance criterion met and backed by evidence.
</mission>

<operating_context>
- This is a multi-homework training repo. `homework-1/` already contains a FastAPI banking
  API. Read it first and match its conventions: project layout, naming, test style, tooling.
  Reuse its patterns instead of inventing new ones.
- `homework-2/` currently contains only `TASKS.md`, a stub `README.md` (mislabeled
  "Homework 1"), and empty `src/`, `demo/`, `docs/screenshots/` dirs. You start from scratch.
- Tech stack is fixed: Python 3.11+ / FastAPI / Pydantic v2 / pytest + pytest-cov / uvicorn.
  Chosen for consistency with homework-1. Keep this stack.
- All paths below are relative to `homework-2/`.
</operating_context>

<how_to_work>
Work as an autonomous agent. Follow these working practices, which are tuned to how the
latest Claude models perform best:

- Investigate before asserting. Read `TASKS.md` in full and open the relevant `homework-1/`
  files before writing or claiming anything about them. Base every statement on files you
  have actually opened, not on assumptions or memory of a summary.
- Read in parallel. When you need several files and the reads are independent, read them in
  the same turn rather than one at a time, to build context faster.
- Develop test-first (TDD). For each unit of behavior, follow red → green → refactor: write a
  failing test that pins the requirement, run it and watch it fail for the right reason,
  implement the minimum correct code to pass, then refactor for clarity with the test green.
  Never write a test you have already seen pass for the wrong reason, and never weaken a test to
  make it pass. The required test files in Task 3 should emerge from this process; add any
  remaining ones afterward to meet the counts and the coverage bar.
- Make steady, incremental progress. Complete one component fully (failing test → implementation
  → green → refactor) before moving to the next. Commit logically-grouped work with git as you
  go so progress is checkpointed and recoverable.
- Track state in structured form. Maintain a `tests.json` (each test: id, name, status) and a
  short `progress.txt` of what's done and what's next, so the build stays coherent even across
  a context refresh. Discover existing state from the filesystem and git log before continuing.
- Be persistent. This is a large task. Plan to use your full available context; complete the
  work fully rather than wrapping up early. If you near a context limit, save state to
  `progress.txt`/`tests.json` and continue — do not stop with significant work uncommitted.
- Verify your own work with tools. Run the app and the tests; rely on real command output,
  not belief, to judge whether something works.
- Act on safe operations directly (creating/editing files in `homework-2/`, running tests).
  Confirm with the user before anything destructive or hard to reverse (deleting unrelated
  files, force-push, touching files outside `homework-2/`). Never bypass safety checks
  (e.g. `--no-verify`) as a shortcut.
- Clean up. Remove any throwaway scratch files you create for iteration before you finish.
</how_to_work>

<context_model_prompt_framework>
This assignment is graded on applying the workshop's Context → Model → Prompt method.
Demonstrate it in how you work and record it in the docs:
- Context: keep the full requirement set in view; ground each implementation decision in the
  specific `TASKS.md` requirement it satisfies (quote the requirement in your plan).
- Model: decompose and reason step by step. For the documentation deliverable (Task 4), the
  spec requires using different AI models for different doc types — record, in each doc's
  footer, which model/approach fits that audience and why.
- Prompt: structure your own working method as Steps → Constraints → Output → Verification,
  mirroring the workshop's structured-prompt template.
</context_model_prompt_framework>

<engineering_principles>
- Clean layering: routes (HTTP) → services (business logic) → repository/store (persistence)
  → models/schemas (Pydantic). Keep business logic out of route handlers.
- Pydantic v2 models perform all validation. Enums are real `enum.Enum` classes shared across
  the codebase (one definition, imported everywhere).
- Full type hints and docstrings on public functions. Centralized error handling returns a
  consistent JSON error envelope; callers never receive a raw stack trace.
- Isolate the CSV/JSON/XML parsers behind a common interface so each is independently testable.
  Parse XML safely (use `defusedxml` or disable external entities) to prevent XXE.
- Validate at system boundaries (request bodies, imported files). Trust internal calls.
- Write a general, correct solution. Implement the actual logic that works for all valid
  inputs — not just the inputs the tests happen to use. Tests verify correctness; they do not
  define it. Do not hard-code values to satisfy a specific test, and do not add helper-script
  workarounds in place of the real implementation. If a requirement seems infeasible or a test
  would be incorrect, say so rather than working around it.
- Build exactly what the spec requires, to a high standard — then stop. Do not add features,
  configuration, or speculative abstractions beyond `TASKS.md`. "Complete" means every listed
  requirement is met well; it does not mean inventing scope. The right amount of complexity is
  the minimum that fully and robustly satisfies the spec.
</engineering_principles>

<quality_bar>
Coverage and test counts are a floor, not the goal. Aim for genuinely high quality across
tests, code, design, and packaging.

Test quality:
- Test behavior and contracts, not implementation details. Each test asserts one clear thing
  and is named for the behavior it pins (e.g. `test_import_rejects_invalid_email`).
- Structure tests Arrange–Act–Assert. Keep them deterministic and independent — no shared
  mutable state, no reliance on test ordering, no real network/clock/random; inject or freeze
  those. Use fixtures for setup and `pytest.mark.parametrize` for input variations.
- Cover the matrix, not just the happy path: valid cases, each validation failure (bad email,
  too-short/too-long strings, invalid enum values), boundary values (1/200 and 10/2000 char
  limits), empty input, malformed files per format, and not-found/error paths.
- Aim for meaningful branch coverage, not just line coverage padded with trivial asserts.
  Every error branch and every enum/priority rule should have a test that would fail if the
  logic were wrong. Performance tests assert real bounds (e.g. import of N rows under a
  threshold), not just "it ran".
- Keep the suite fast and green; no skipped or xfail tests left unexplained.

Code & design quality:
- Single-responsibility modules; clear separation of routes/services/repository/models.
- Descriptive names, no dead code, no copy-paste duplication (DRY), low function complexity.
- Explicit, typed function signatures; meaningful return types; no bare `except:`.
- Structured logging for classification decisions and import errors (not `print`).
- Configuration via environment/settings, not hard-coded constants scattered in code.

Package & tooling quality:
- A proper `pyproject.toml` (project metadata, pinned/compatible deps, dev-deps, tool config).
- Configure and pass: a formatter (`black` or `ruff format`), a linter (`ruff`), and a type
  checker (`mypy`, reasonable strictness). The codebase must be clean under all three.
- A `.gitignore`, a runnable entrypoint (`uvicorn`), and a convenience runner (a `Makefile`
  or `init.sh` exposing `install`, `run`, `test`, `lint`, `typecheck`, `coverage`) so the
  project starts, tests, and checks reproducibly with one command each.
</quality_bar>

<integrity_rules>
These protect the trustworthiness of the result. Treat them as non-negotiable.
- Report only real results. State a coverage %, a test count, or "it works" only when you are
  quoting actual output from a command you just ran. Run `pytest` and `pytest --cov` and quote
  the real numbers. Never fabricate or estimate them.
- Use only APIs and libraries you are certain exist. If unsure of a signature, choose a
  standard-library or well-known approach you can verify.
- If you do not know something, say so plainly instead of guessing.
- If a requirement is genuinely ambiguous or underspecified, record the ambiguity and the
  assumption you chose in `ASSUMPTIONS.md`, pick the most standard defensible interpretation,
  and proceed — do not stall and do not silently guess.
- Keep full traceability: every acceptance criterion maps to real code plus a real test. If
  one cannot be met, flag it openly in the final report rather than papering over it.
</integrity_rules>

<requirements_authoritative>
Implement ALL of the following. Treat each bullet as a checklist item. (This restates
`TASKS.md`; if anything here seems to differ from `TASKS.md`, re-read `TASKS.md` and treat it
as authoritative.)

TASK 1 — Multi-Format Ticket Import API:
- Endpoints (exact): `POST /tickets`, `POST /tickets/import`, `GET /tickets` (with filtering),
  `GET /tickets/{id}`, `PUT /tickets/{id}`, `DELETE /tickets/{id}`.
- Ticket model fields & types exactly as in TASKS.md: id(UUID), customer_id, customer_email
  (valid email), customer_name, subject(1–200 chars), description(10–2000 chars),
  category(enum: account_access|technical_issue|billing_question|feature_request|bug_report|other),
  priority(enum: urgent|high|medium|low),
  status(enum: new|in_progress|waiting_customer|resolved|closed),
  created_at, updated_at, resolved_at(nullable), assigned_to(nullable), tags(array),
  metadata{ source(enum: web_form|email|api|chat|phone), browser, device_type(enum: desktop|mobile|tablet) }.
- Parse CSV, JSON, and XML import files. Validate every required field (email format, string
  length bounds, enum membership).
- Bulk import returns a summary: total records, successful count, failed count, and per-row
  error details.
- Malformed files fail gracefully with a meaningful message (return a 400-class error, never a
  raw 500/stack trace to the caller).
- Use correct HTTP status codes (e.g. 201 created, 200 ok, 400/422 validation, 404 not found).

TASK 2 — Auto-Classification:
- `POST /tickets/{id}/auto-classify` returns: category, priority, confidence (0–1),
  reasoning (human-readable), keywords_found (list).
- Category rules per TASKS.md (account_access / technical_issue / billing_question /
  feature_request / bug_report / other).
- Priority keyword rules: Urgent = "can't access", "critical", "production down", "security";
  High = "important", "blocking", "asap"; Low = "minor", "cosmetic", "suggestion";
  Medium = default.
- Support optional auto-run on ticket creation (flag), store the classification confidence,
  allow manual override, and log every classification decision.

TASK 3 — Test Suite (coverage strictly greater than 85%, measured, not claimed):
- Files meeting at least these test counts: test_ticket_api (11), test_ticket_model (9),
  test_import_csv (6), test_import_json (5), test_import_xml (5), test_categorization (10),
  test_integration (5), test_performance (5), plus a `fixtures/` dir with sample data.
- Prove overall line coverage > 85% with real `pytest --cov` output.

TASK 4 — Multi-Level Documentation (in `docs/`):
- README.md (developers): overview + features, a Mermaid architecture diagram, install/setup,
  how to run tests, project structure. Also fix the mislabeled `homework-2/README.md`.
- API_REFERENCE.md (API consumers): every endpoint with request/response examples, data
  models/schemas, error formats, and a cURL example per endpoint.
- ARCHITECTURE.md (tech leads): a high-level Mermaid diagram, component descriptions, Mermaid
  sequence diagrams for data flow, design decisions/trade-offs, security & performance notes.
- TESTING_GUIDE.md (QA): a Mermaid test-pyramid diagram, how to run tests, fixture locations,
  a manual testing checklist, and a performance-benchmark table.
- Use a different AI model/approach per doc type (note which, per doc). Include at least 3
  Mermaid diagrams across the documents.

TASK 5 — Integration & Performance:
- A complete ticket-lifecycle workflow test; a bulk-import + auto-classify verification test;
  a concurrency test firing 20+ simultaneous requests; and a combined category-AND-priority
  filtering test.

DELIVERABLES:
- Runnable source under `src/`.
- A coverage report, plus a screenshot at `docs/screenshots/test_coverage.png`. Generate the
  HTML/terminal coverage report. If you cannot capture a real PNG yourself, produce the report
  and state explicitly that a human must capture the screenshot — do not fabricate the image.
- Sample data: `sample_tickets.csv` (50 records), `sample_tickets.json` (20),
  `sample_tickets.xml` (30), plus invalid-data files for negative tests.
</requirements_authoritative>

<examples>
These show the exact shape of two outputs. Match their structure; the values are illustrative.

<example name="auto-classify response">
Request: auto-classify a ticket whose description is
"I can't access my account after the update — this is critical, production is down for my team."
Expected response body:
{
  "category": "account_access",
  "priority": "urgent",
  "confidence": 0.93,
  "reasoning": "Describes inability to log in (account_access signal) and contains the urgent keywords 'critical' and 'production down'.",
  "keywords_found": ["can't access", "critical", "production down"]
}
</example>

<example name="self-verification report row">
| Requirement | Status | Evidence |
|---|---|---|
| POST /tickets/import parses XML and rejects malformed XML | ✅ | src/services/import_service.py:88 (defusedxml); tests/test_import_xml.py — 5 tests, all pass |
| Coverage > 85% | ✅ | `pytest --cov` → TOTAL 92% (paste real summary line) |
</example>
</examples>

<workflow>
Reason through the work and show your plan before coding. Proceed in this order:
1. PLAN: Read `TASKS.md` fully and skim `homework-1/`. Produce a build plan and a
   requirement → file → test traceability table, quoting each requirement. Create
   `ASSUMPTIONS.md` for any gaps. Initialize `progress.txt` and `tests.json`.
2. SCAFFOLD: Create the project structure, `pyproject.toml`, app entrypoint, `.gitignore`,
   and the runner (`Makefile`/`init.sh`). Configure `ruff`, `black`/`ruff format`, `mypy`,
   and `pytest`/`pytest-cov`. Confirm an empty `pytest` run and the lint/type tooling execute.
3. BUILD EACH COMPONENT TEST-FIRST (red → green → refactor), in this order, keeping the suite
   green after each: (a) models — Pydantic schemas, shared enums, validation; (b) repository/
   store; (c) CRUD + filtering endpoints; (d) CSV/JSON/XML import + import summary + graceful
   malformed handling; (e) classifier rules engine + endpoint + decision logging; (f)
   integration + performance scenarios. For each: write the failing test(s) first, implement
   the minimum correct code, then refactor.
4. COVERAGE & COUNTS: ensure every required test file exists and meets its minimum count; run
   `pytest --cov`; if coverage ≤ 85% or a real branch is untested, add targeted tests and
   repeat until > 85% with meaningful assertions.
5. QUALITY GATES: run the formatter, `ruff`, and `mypy`; fix all findings until clean.
6. SAMPLE DATA: generate the CSV/JSON/XML datasets and the invalid files.
7. DOCS: write all doc files with the required Mermaid diagrams and cURL examples (Task 4).
8. VERIFY: run the chain-of-verification below; fix every failure; re-run until all pass.
9. REPORT: produce the self-verification report.
Keep `progress.txt`/`tests.json` and git commits updated as you complete each step.
</workflow>

<chain_of_verification>
When you believe the build is complete, do not trust it — verify. Answer each question below
against the actual code and real command output, citing a file path or output line. Fix every
NO and re-verify until all are YES:
- Do all 6 Task-1 endpoints exist with the correct verb, path, and status codes?
- Are all enum fields rejecting invalid values (tested)?
- Are subject/description length bounds and email format enforced (tested)?
- Do CSV, JSON, and XML imports each parse a valid file AND reject a malformed one gracefully?
- Does the import summary report total / successful / failed with per-row error details?
- Does auto-classify return category, priority, confidence ∈ [0,1], reasoning, keywords_found?
- Do the priority keyword rules produce the documented priority for each keyword set?
- Do all required test files exist and meet their minimum test counts?
- Did `pytest` pass with 0 failures, with no unexplained skipped/xfail tests? (quote the line)
- Is measured coverage strictly > 85%? (quote the real `--cov` total)
- Do the linter (`ruff`), formatter, and `mypy` all pass clean? (quote each result)
- Are validation-failure and error branches covered by tests that would fail if the logic
  were wrong (not just happy-path tests padding line coverage)?
- Does the runner (`Makefile`/`init.sh`) start the app and run test/lint/typecheck reproducibly?
- Does the concurrency test actually issue 20+ simultaneous requests and assert success?
- Are there ≥ 3 Mermaid diagrams across the docs, and a cURL example for every endpoint?
- Do the sample files contain exactly 50 CSV / 20 JSON / 30 XML records, plus invalid files?
- Is `homework-2/README.md` correctly titled (not "Homework 1")?
</chain_of_verification>

<output_format>
1. The built files in the repo are the primary output.
2. Finish with a Self-Verification Report (markdown) containing:
   - A requirement → status (✅/❌) → evidence (path / command output) table covering every
     bullet in <requirements_authoritative> (see the example row above).
   - The real `pytest` summary line and the real coverage total.
   - The contents of `ASSUMPTIONS.md`.
   - An honest "Known gaps / human-required steps" section (e.g. capturing the coverage PNG).
3. Keep prose tight. Prioritize working artifacts and verifiable evidence over narration.
</output_format>

<quality_gates>
The deliverable is complete only when all of these hold:
[ ] All 6 CRUD/import endpoints + the auto-classify endpoint are implemented and tested.
[ ] CSV + JSON + XML import all work and fail gracefully on malformed input.
[ ] All validation rules (enums, lengths, email) are enforced and tested.
[ ] All required test files exist and meet their minimum counts.
[ ] `pytest` passes with 0 failures, no unexplained skips (real output quoted).
[ ] Coverage is strictly > 85%, including error/validation branches (real output quoted).
[ ] Linter, formatter, and `mypy` all pass clean (real output quoted).
[ ] The runner (`Makefile`/`init.sh`) reproducibly does install / run / test / lint / typecheck.
[ ] The 20+ concurrent-request test passes.
[ ] 4 doc files exist, with ≥ 3 Mermaid diagrams, a cURL example per endpoint, and a per-doc
    model note.
[ ] Sample data present: 50 CSV / 20 JSON / 30 XML + invalid files.
[ ] README correctly titled; `ASSUMPTIONS.md` present; Self-Verification Report produced.
If any box is unchecked, keep working — do not declare success.
</quality_gates>

Begin with Step 1 (PLAN): show the plan and the requirement → file → test traceability table,
quoting each requirement, before writing any code.

=== PROMPT END ===

---

## Meta-notes (for the human — do not paste)

### Recommended run settings (Claude Opus 4.8)
Per Anthropic's current guidance, for coding/agentic work:
- **Effort:** `xhigh` (best for coding/agentic; use `high` minimum). `max` can overthink.
- **Thinking:** `{type: "adaptive"}` (off by default on 4.8 unless set; adaptive beats fixed).
- **max_tokens:** start at **64k** so the model has room to think and act across the build.
- In Claude Code, this maps to running at high/xhigh effort and letting it work autonomously.

### What changed in this refinement and why (grounded in Anthropic's prompting docs)
| Change | Source principle |
|---|---|
| Softened ALL-CAPS "CRITICAL/MUST/HARD rules" to firm-but-normal language | Newer models *overtrigger* on aggressive language; "use more normal prompting" |
| Added `<examples>` (classify response + report row) in tags | "Examples are one of the most reliable ways to steer output"; wrap in `<example>` tags |
| Added **anti-hard-coding / general-solution** language | Anthropic's "avoid focusing on passing tests and hard-coding" snippet — critical when AI also writes the tests |
| Added **anti-overengineering / build-to-spec-then-stop** | Opus 4.5/4.6/4.8 tendency to overengineer; balances "be thorough" without inventing scope |
| Added `<how_to_work>`: investigate-before-asserting, parallel reads, git checkpoints, `tests.json`/`progress.txt` state, persistence, cleanup, autonomy/safety | Anthropic agentic + long-horizon, state-tracking, hallucination, and safety guidance |
| Added **TDD (red→green→refactor)** as the dev methodology + workflow | Tests-first improves correctness and design; pairs with Anthropic's "write tests first / keep them" long-horizon guidance |
| Added `<quality_bar>`: test-quality criteria (AAA, parametrize, branch coverage, boundaries/negatives), code/design quality (SRP, DRY, typing, structured logging), package/tooling quality (`pyproject`, `ruff`+`black`+`mypy`, runner) | Coverage % alone games quality; explicit quality attributes + tooling gates make "quality" concrete and checkable |
| Added "ground each decision in the quoted requirement" | Long-context "ground responses in quotes" technique |
| Kept XML structure, explicit scope, restated spec, CoVe, quality gates, uncertainty clause | Already aligned with: XML tags, literal instruction following, self-check, define success criteria |
| Moved the actual task ("Begin with Step 1") to the very end | Long-context: put the query at the end (up to ~30% quality gain) |

### Techniques deliberately *not* added
- **Prefill** — deprecated on Claude 4.6+; replaced by direct instruction + structured outputs.
- **Heavy step-by-step reasoning scripting** — Anthropic notes "think thoroughly" often beats a
  hand-written reasoning script; the workflow here lists *deliverables/order*, not how to reason.
- **CoT everywhere** — 2025 research shows CoT can *raise* hallucination on open-ended factual
  questions; harmless here (this task has ground truth via the spec + runnable tests).

### Sources
- [Anthropic — Prompting best practices (Claude Opus 4.8 / latest)](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Anthropic — Prompt engineering overview](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/overview)
- [Best practices for prompt engineering — Claude](https://claude.com/blog/best-practices-for-prompt-engineering)
- [Cut AI Hallucinations: 5 prompt patterns (2026)](https://www.keepmyprompts.com/en/blog/reduce-ai-hallucinations-better-prompts-practical-guide)
- [Reducing AI hallucinations: 6 techniques](https://medium.com/@aysan.nazarmohamady/reducing-ai-hallucinations-6-prompt-engineering-techniques-that-actually-work-16b583797bd0)

To use it: open a fresh session in the repo root, paste the PROMPT block, let it run. If you'd
like, I can execute this prompt myself now and build homework-2.
