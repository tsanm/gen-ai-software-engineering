# agents.md — AI Coding Partner Guidelines (Virtual Card Lifecycle)

These rules tell an AI coding agent how to behave when implementing `specification.md`. They
are **binding defaults**: when the spec and a convenient shortcut conflict, follow the spec and
these rules. When in doubt in a FinTech context, choose the **safer, more auditable** option and
say so.

## 1. Tech stack assumptions

- **Language/runtime:** Python 3.11+ (the spec is language-agnostic; if another stack is chosen,
  preserve every rule below). **Web:** FastAPI. **Validation:** Pydantic v2. **Tests:** pytest +
  coverage. **Tooling gate:** ruff (lint+imports), mypy (types), bandit (security), radon
  (complexity). All must pass before a change is "done".
- **Money:** integer **minor units** + ISO-4217 `currency`; use `Decimal` for arithmetic, never
  binary `float`. Round half-even only at presentation.
- **Persistence:** an abstracted repository (in-memory acceptable for the exercise) — **no PAN or
  CVV is ever stored** in this service.
- **External services** (treat as injected, mockable clients): identity/auth, PAN vault,
  transaction stream/ledger, notification service, audit store.

## 2. Domain rules (banking / FinTech)

- **PCI scope minimization is non-negotiable.** Reference cards by `card_token` + `last4` only.
  If a task seems to require a PAN/CVV in this service, **stop and flag it** — do not invent a
  field to store it.
- **The state machine is the only way `status` changes.** Route every transition through the
  guarded `transition()` function; never assign `status` directly in an endpoint.
- **Authorization is a pure function** of (card snapshot, candidate transaction, window usage).
  No I/O inside it, so it stays deterministic, testable, and replayable.
- **Fail closed.** On any uncertainty in a money-gating path (missing data, dependency down),
  **decline / reject**, never approve. Issuance fails closed too (no card row if the vault fails).
- **Idempotency by default.** Every state-changing operation accepts an `Idempotency-Key`; a
  replay must not produce a second state change or a duplicate audit event.
- **Everything sensitive is audited, nothing sensitive is logged** (see §4, §5).

## 3. Code style & structure

- **Layered, dependencies inward:** `api → services → domain → repo/integrations`. API handlers
  are thin; business and domain logic live below them. Domain (`card`, `lifecycle`, `authorize`)
  has **no framework or I/O imports**.
- Full type hints; small, single-responsibility functions; keep cyclomatic complexity low (no
  radon C-or-worse blocks). Descriptive names; no dead code; DRY.
- One **error envelope** `{error, message, details, requestId}` with stable machine `error`
  codes; map domain errors to HTTP codes per the spec's Implementation Notes.
- All timestamps UTC, ISO-8601. All responses carry `X-Request-ID`.

## 4. Testing & verification expectations

- **TDD preferred:** write the failing test for a behavior, implement minimally, refactor.
- **Required coverage of behavior, not just lines:** for each decision branch in `evaluate`
  (frozen, terminated, per-txn over, rolling over, currency mismatch, approve, fail-closed) there
  must be a test, **including the exact boundary** (`amount == limit` approves; `+1` declines).
- **State machine:** a test per legal transition and ≥3 illegal ones.
- **Idempotency & concurrency:** tests proving replay creates no duplicate audit, and that a
  stale-version write returns `409`.
- **Audit integrity:** a test that tampering breaks `verify_chain()`.
- **Negative/permission tests:** ownership `403` and role `403` with **no existence disclosure**.
- Treat the spec's *Verification* and *Edge Cases* tables as the test backlog. Aim high
  (≥ the project's coverage gate) but never pad with assertion-free tests.

## 5. Security & compliance constraints (hard rules)

- **NEVER log, trace, print, or include in errors:** PAN, CVV, full PII, or raw tokens. Log only
  `card_id`, opaque `owner_id`, and `last4` where strictly needed.
- **Default-deny authorization** on every endpoint: verify the JWT, enforce **ownership**
  (user acts only on own cards) and **role** (`user` vs `ops`). Ops access to another user's card
  is itself audited.
- **Audit and state change are one transaction** — never commit a state change without its audit
  record.
- **No secrets in code or logs**; rely on injected config/KMS. bandit must pass.
- **Input validation at the boundary**; reject unknown/extra fields on sensitive payloads.

## 6. How to treat edge cases (defaults)

- Prefer **idempotent writes**; design every mutation to be safely retryable.
- On a dependency timeout in a money path → **fail closed** with `503 dependency_down` or a
  decline, never a silent success.
- Validation failures → `400` with the envelope; illegal state transitions → `422`; ownership/
  role → `403`/`404` (no existence leak); idempotency mismatch → `409`.
- Empty states return empty results (`200` + empty list), not errors.
- When the spec is ambiguous, **do not guess silently**: pick the most standard, auditable
  interpretation, implement it, and record the assumption (e.g. in an `ASSUMPTIONS.md`).

## 7. What the agent must NOT do

- Do not add a PAN/CVV field, log sensitive data, or weaken `verify_chain()`.
- Do not mutate `status` outside the guarded transition, or make `evaluate` impure.
- Do not approve on uncertainty, skip the audit write, or bypass idempotency.
- Do not introduce floats for money, or compare amounts across currencies.
- Do not expand scope (settlement, KYC, fraud *decisions*) — those are out of scope; expose
  hooks instead.
