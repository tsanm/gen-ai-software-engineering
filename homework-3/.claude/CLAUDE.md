# CLAUDE.md — Virtual Card Lifecycle

Always-loaded steering for *how* to work in this repo. The **what** lives in
[`specification.md`](../specification.md) (objectives M1–M7, tasks, edge cases, verification,
SLOs); the vendor-neutral agent contract is [`agents.md`](../agents.md) (the `AGENTS.md` convention)
— this file is just its Claude-specific, always-loaded subset. **On any conflict, the spec wins.** (In a live repo this sits at the project root to auto-load; it is under `.claude/` here to
match the homework deliverable.)

## Before any change
1. Open the spec — don't work from memory of a summary. Read the task/objective you're touching.
2. Cite it: every change names a task/objective id (e.g. "Task 9 → M3") and must not violate a
   constraint from another spec section.

## Golden rules — FinTech, never violate
High-blast-radius and non-default; `agents.md` §2/§6 carry the full versions.
- **Never** store, log, trace, print, or return a **PAN or CVV**. Reference cards by `card_token`
  + `last4` only. If a task seems to need a PAN, **stop and ask** — do not add the field.
- **Fail closed.** In any money-gating path (authorization, issuance), missing data or a
  dependency timeout means **decline/reject**, never approve.
- **State changes only through the guarded `transition()`** — never assign `status` directly.
- **`evaluate()` (authorization) stays pure** — no I/O, deterministic, replay-safe.
- **Every mutation is idempotent (`Idempotency-Key`) and audited in the same transaction** — a
  replay creates no second state change and no duplicate audit event.
- **Default-deny.** Verify JWT; enforce ownership + role on every endpoint; never disclose others'
  cards (`403`/`404`); an ops read of another user's card is itself audited.

## Non-inferable conventions
Generic style is enforced by the gate below; these are the domain rules an agent gets wrong by default.
- **Money:** integer minor units + ISO-4217 `currency`; `Decimal` for math, **never `float`**;
  never compare across currencies.
- **Errors:** one envelope `{error, message, details, requestId}` using only the stable codes in
  the spec's **Error Code Catalog** — the single source of truth; don't invent codes or HTTP
  mappings. No stack traces to clients.
- **Layering:** `api → services → domain → repo/integrations`, dependencies inward; keep `domain/`
  (`card`, `lifecycle`, `authorize`) free of framework/I/O imports. IDs and time rules per the spec's
  *Implementation Notes*; workflow per `agents.md` §3.

## Definition of done (the check you must run)
- Traces to a task/objective; honors all spec constraints.
- Behavior **and its boundary** tested (`amount == limit` approves, `+1` declines); legal +
  illegal transitions; replay + concurrency where relevant.
- `ruff && mypy && bandit && radon (no C+) && pytest` (coverage gate) all green.
- No PAN/CVV/PII in code, logs, or tests; an audit event exists for every state change.

## Never
- Mutate `status` outside `transition()`, or make `evaluate()` impure.
- Approve on uncertainty; skip the audit write; bypass idempotency.
- Use `float` money or cross-currency comparison; put a secret/PAN/token in code, logs, or a URL.
- Expand scope into settlement, KYC, or fraud *decisions* — expose hooks, don't implement them.
- Guess on ambiguity — pick the safest auditable option and record it in `ASSUMPTIONS.md`.
