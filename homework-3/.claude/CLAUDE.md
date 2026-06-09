# CLAUDE.md — Project Rules (Virtual Card Lifecycle)

Claude Code memory for this project. (In a live repo this lives at the project root so it
auto-loads; it is placed under `.claude/` here to match the homework deliverable.) It steers
*how* to work; the **what** is in [`specification.md`](../specification.md) and the full agent
manual is in [`agents.md`](../agents.md). On any conflict, the spec wins.

## Read first
1. `specification.md` — objectives (M1–M7), constraints, edge cases, verification, performance.
2. `agents.md` — domain/security/testing rules.
Ground every change in a specific objective or task id (e.g. "implements Task 9 → M3"). Do not
implement from memory of a summary — open the file.

## Golden rules (FinTech defaults — never violate)
- **Never** store, log, trace, print, or return a **PAN or CVV**. Reference cards by
  `card_token` + `last4` only. If a task seems to need a PAN here, **stop and ask** — do not add
  the field.
- **Fail closed** in any money-gating path: on missing data or a dependency timeout, **decline /
  reject**, never approve. Card issuance fails closed too.
- **State changes only through the guarded `transition()`** — never assign `status` directly.
- **`evaluate()` (authorization) is pure** — no I/O, deterministic, replay-safe.
- **Every mutation is idempotent** (`Idempotency-Key`) and **audited in the same transaction**;
  a replay must create no second state change and no duplicate audit event.
- **Default-deny**: verify JWT, enforce ownership + role on every endpoint; ops access to another
  user's card is itself audited; never disclose existence of others' cards (`403`/`404`).

## Conventions
- **Layering (deps point inward):** `api → services → domain → repo/integrations`. Keep `domain/`
  (`card`, `lifecycle`, `authorize`) free of framework/I/O imports. Thin API handlers.
- **Naming:** modules `snake_case`; types `PascalCase`; money fields end in `_minor` (integer
  minor units) and travel with a `currency`; ids are `card_id`, `owner_id`, `txn_id`, UUIDv4.
- **Money:** integer minor units; `Decimal` for math; **never `float`**; never compare across
  currencies.
- **Errors:** one envelope `{error, message, details, requestId}` with stable machine codes
  (`card_frozen`, `limit_exceeded`, `invalid_transition`, `idempotency_conflict`, `forbidden`,
  `not_found`, `dependency_down`). Map to HTTP per the spec. No stack traces to clients.
- **Time:** UTC, ISO-8601; server is the clock of record. Every response carries `X-Request-ID`.

## Definition of done (per change)
- Traces to an objective/task; respects all spec constraints.
- Tests cover the behavior **and its boundary** (e.g. `amount == limit` approves, `+1` declines);
  legal + illegal transitions; replay + concurrency where relevant.
- `ruff`, `mypy`, `bandit`, `radon` (no C+), and `pytest` (meet the coverage gate) all pass.
- No PAN/CVV/PII in code, logs, or tests; audit emitted for every state change.

## Avoid
- Mutating `status` outside `transition()`; making `evaluate()` impure.
- Approving on uncertainty; skipping the audit write; bypassing idempotency.
- `float` money; cross-currency comparison; secrets in code/logs.
- Scope creep into settlement, KYC, or fraud *decisions* — expose hooks, don't implement them.
- Guessing on ambiguity — pick the safest auditable option and record it in `ASSUMPTIONS.md`.
