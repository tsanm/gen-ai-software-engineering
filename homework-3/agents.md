# agents.md — AI Operating Contract (Virtual Card Lifecycle)

How an AI agent must **behave** when implementing this feature. The authoritative **requirements**
live in [`specification.md`](specification.md) (objectives M1–M7, tasks, edge cases, the
**Error Code Catalog**, SLOs); [`.claude/CLAUDE.md`](.claude/CLAUDE.md) is the always-loaded subset
of the rules below. To prevent drift, each concern has **one source of truth**: this file owns
*agent behavior and workflow*; the spec owns *requirements and the exact numbers, codes, and tables*.
**On any conflict, the spec wins.** In FinTech doubt, choose the safer, more auditable option and say so.

## 1. Tech stack & quality gate
- **Python 3.11+**, **FastAPI**, **Pydantic v2**, **pytest** + coverage. The spec is
  language-agnostic; if the stack changes, every rule below still holds.
- **External services are injected, mockable clients:** identity/auth, PAN vault, transaction
  stream/ledger, notifications, audit store *(spec → Context → Beginning context)*.
- **Definition of done = this gate is green:** `ruff` (lint+imports), `mypy` (types), `bandit`
  (security), `radon` (no C-or-worse complexity), `pytest` (meet the coverage gate) — and the change
  traces to a task/objective. Show the passing output as evidence; don't assert success.
- While iterating, run **file-scoped** checks for speed (e.g. `pytest path/to/test_x.py`); run the
  full gate before calling a change done.

## 2. Non-negotiables (behavioral defaults)
Internalize these so you apply them without re-reading; the exact codes/numbers stay in the spec.
- **Closed-world spec.** Build only what `specification.md` defines; do **not** invent endpoints,
  fields, status values, error codes, or dependencies beyond it. Missing or conflicting → stop and
  ask. *(spec → Authority & sources of truth)*
- **PCI scope minimization.** Never store, log, or return a **PAN or CVV**; reference cards by
  `card_token` + `last4`. If a task seems to need a PAN, **stop and flag it** — don't add the field.
  *(spec → Security; Implementation Notes → IDs)*
- **Fail closed** in every money-gating path (authorization, issuance): missing data or a dependency
  timeout means **decline/reject**, never approve. *(spec → Reliability; Tasks 4, 10)*
- **State changes only through the guarded `transition()`**; never assign `status` directly.
  *(spec → Domain Model; Tasks 2, 13)*
- **`evaluate()` is a pure function** of (card snapshot, candidate txn, window usage) — no I/O,
  deterministic, replay-safe. *(spec → Determinism; Task 10)*
- **Idempotent + audited together.** Every mutation takes an `Idempotency-Key` and writes its audit
  event in the same transaction; a replay yields no second state change and no duplicate audit.
  *(spec → Implementation Notes, Audit; Tasks 5, 6)*
- **Default-deny.** Verify the principal; enforce ownership + role on every endpoint; another user's
  card → `404` (never `403`, no existence leak), `403` only for role failures; audit ops reads of
  another user's card. *(spec → Security; Error Catalog → Mapping rules; E10, E11)*
- **Money & errors** exactly as the spec defines: integer minor units + `Decimal`, never `float`, no
  cross-currency comparison; one error envelope using only the **Error Code Catalog**.

## 3. Workflow
- **Explore → plan → implement.** For any multi-file task, read the relevant spec sections (and any
  existing code) first, state the plan, then code. Skip planning only for one-line changes.
- **Ground every change in a task/objective id** (e.g. "Task 9 → M3") and never implement it in a way
  that violates a constraint from another spec section.
- **Dependency order.** Tasks are ordered foundations → behavior → cross-cutting → verification;
  finish each task's DoD before starting the next.
- **TDD.** Write the failing test for the behavior — *including its boundary* — implement minimally,
  refactor.
- **On ambiguity, don't guess silently:** pick the most standard, auditable interpretation,
  implement it, and record it in `ASSUMPTIONS.md`.
- **Layering:** `api → services → domain → repo/integrations`, dependencies inward; thin handlers;
  `domain/` (`card`, `lifecycle`, `authorize`) has no framework/I/O imports. Pure data models
  (Pydantic/dataclasses) are fine in `domain/`; "no I/O" means no network/db/file/clock calls. Typed
  error *classes* live in `domain/` (HTTP mapping in `platform/`). Full type hints, small functions, no dead code.

## 4. Testing expectations
Treat the spec's **Verification** and **Edge Cases** tables as the test backlog. Minimum bar:
- `evaluate` decision matrix incl. the exact boundary (`amount == limit` approves, `+1` declines)
  and every decline reason; the state machine's legal + ≥3 illegal transitions.
- Replay creates no duplicate audit; a stale-version write → `409`; tampering breaks `verify_chain()`.
- Ownership `403` and role `403` with **no existence disclosure**; empty states → `200` + empty list.
- Aim ≥ the coverage gate, but never pad with assertion-free tests.

## 5. Autonomy boundaries (what needs a human)
- **Proceed autonomously:** read code/spec; write and run tests; run lint/type/security/complexity
  checks; implement a task within its stated scope and DoD.
- **Stop and ask first:** add or upgrade a dependency; change the data model, audit schema, or
  anything touching PII retention; relax a security/compliance control or the quality gate; widen
  PCI scope or anything that seems to require a PAN; go beyond the task's `→ M#` scope.
- **Secrets:** document *where* keys/credentials live (injected config / KMS) — never put them in
  code, logs, or this file. Treat every file in this repo as potentially public.

## 6. Never
- Add a PAN/CVV field; log sensitive data; weaken `verify_chain()`.
- Mutate `status` outside `transition()`; make `evaluate()` impure.
- Approve on uncertainty; skip the audit write; bypass idempotency.
- Use `float` money or compare across currencies; put a secret/PAN/token in code, logs, or a URL.
- Expand scope into settlement, KYC, or fraud *decisions* — expose hooks instead.
