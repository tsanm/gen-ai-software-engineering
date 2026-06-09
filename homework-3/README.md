# 💳 Homework 3: Specification-Driven Design — Virtual Card Lifecycle

> **Student:** Anton Tsiatsko · **Course:** AI-Assisted Development
> **Deliverable type:** specification package only — **no implementation** (per `TASKS.md`).

## Task summary

Design a **layered specification package** for a finance feature in a regulated environment.
I chose the **virtual card lifecycle** (the flagship example in `TASKS.md`): a user can issue a
card, freeze/unfreeze it, set spending limits, and view its transactions, while an internal
ops/compliance role can inspect any card and its immutable audit trail. The graded artifact is
the spec's depth, its traceability from goals to tasks, and the rationale below — not code.

### Files in this package

| File | Purpose |
|------|---------|
| [`specification.md`](specification.md) | The layered spec: High-level → Mid-level (M1–M7) → Non-functional & policy → Implementation notes → Context → 20 low-level tasks, plus integrated **Edge Cases**, **Verification**, **Performance**, and a **Traceability Matrix**. |
| [`agents.md`](agents.md) | AI coding-partner manual: stack, banking domain rules, code style, testing/verification expectations, security/compliance hard rules, edge-case defaults. |
| [`.claude/CLAUDE.md`](.claude/CLAUDE.md) | Claude Code rules file — concise, imperative "how to work" steering (FinTech golden rules, naming/patterns, DoD, what to avoid). |
| `README.md` | This file: rationale + industry best practices with section references. |

## Rationale — why the spec is written this way

**Layering for executability, not prose.** The spec is built so an engineering team *or an AI
agent* could execute it without guessing. Each layer answers a different question: the
*High-Level Objective* fixes the north star and an explicit **scope boundary** (what this
feature does **not** own — settlement, KYC, PAN storage); the *Mid-Level Objectives* (M1–M7) are
written as **observable signals** so "done" is checkable; *Implementation Notes* encode the
guardrails an agent must not violate; *Low-Level Tasks* decompose into 20 executable slices,
each naming the objective it serves and ending in a **Definition of Done**.

**Traceability was designed in, not bolted on.** Every low-level task carries a `→ M#` tag, and
the closing **Traceability Matrix** maps each objective down to its tasks, edge cases, and
verification method (and back up). This directly targets the homework's grading criterion —
"how traceable requirements are from goals down to tasks."

**Edge cases, verification, and performance are first-class sections**, not a single vague
bullet. They are cross-referenced: edge case `E8` (the limit boundary) is enforced by Task 10,
asserted in the M7 verification row, and bounded by the authorization latency SLO — the same
concern appears consistently across all three lenses.

**How I chose the performance targets.** I budgeted by **where each path sits in the user/ money
flow**, then labelled hypothetical numbers as **(assumed)** with a reason:
- *Authorization evaluation* gets the tightest budget (**p99 ≤ 50 ms**) because it sits inside the
  card-network auth round-trip, which expects sub-100 ms end-to-end — so the in-house slice must
  be small. Its availability target is the highest (99.95%) and it **fails closed**, so its worst
  case is "decline", never "approve".
- *Read endpoints* use **p95 ≤ 200 ms**, the common "feels instant" UX threshold.
- *Writes* get a looser **p95 ≤ 400 ms** because they are infrequent and must include the
  synchronous audit (and, for issuance, the vault call).
- *Pagination* is cursor-based with a max page of 100 to bound payload and avoid deep-offset cost
  while staying stable under concurrent inserts (`E14`).
- *Transaction freshness* is **≤ 5 s** because that read-model is projected from an external
  eventually-consistent stream; the number is surfaced honestly in the UX ("may take a few
  seconds") rather than pretending it is instant.

**How I chose verification depth.** Verification depth follows **blast radius**. The pure
authorization function (M7) gates money, so it gets an exhaustive decision-matrix unit suite
*including the exact boundary* and a purity/determinism property check. The audit trail (M6)
underpins compliance, so it gets an integrity test that must *fail* on tampering. Ownership/role
boundaries get negative tests that also assert **no existence disclosure**. Lower-risk paths
(notifications) get lighter, best-effort verification. The spec lists test categories *as
documentation* because the homework requires no code.

**Why FinTech shaped every layer.** Regulated-environment thinking is woven through the spec
rather than confined to a security essay: PCI scope is minimized at the **data-model** level (no
PAN/CVV stored — only `card_token` + `last4`), idempotency and audit are **cross-cutting tasks**,
and "**fail closed**" is stated as a reliability policy *and* enforced in the authorization task
and the issuance task.

## Industry best practices — what I added and where it appears

| Best practice | Where it appears (file → section) |
|---------------|-----------------------------------|
| **PCI-DSS scope minimization** (never store PAN/CVV; tokenize) | `specification.md` → *Non-Functional & Policy → Security*; *Implementation Notes → IDs*; enforced by *Task 1, 4*; checked in *Verification (M1 schema review)* |
| **Tokenization / vault isolation** | `specification.md` → *Context → Beginning context*; *Task 4 (VaultClient)*; `agents.md` §2 |
| **Immutable, hash-chained audit trail** (tamper-evident, same-transaction) | `specification.md` → *Non-Functional → Audit*; *Task 6*; *Edge E2/E4*; *Verification (M6, `verify_chain`)* |
| **Least privilege + default-deny authZ** (ownership + role; no existence leak) | `specification.md` → *Security*; *Task 8, 11, 12*; *Edge E10/E11*; `.claude/CLAUDE.md` Golden rules |
| **Idempotency for safe retries** | `specification.md` → *Implementation Notes → Idempotency*; *Task 5*; *Edge E2/E3*; `agents.md` §2 |
| **Fail-closed in money paths** | `specification.md` → *Reliability*; *Task 4, 10*; *Edge E1/E9*; `.claude/CLAUDE.md` Golden rules |
| **Money as integer minor units / `Decimal`, never float** | `specification.md` → *Implementation Notes → Money*; *Task 1*; `agents.md` §1; `.claude/CLAUDE.md` Conventions |
| **Explicit state machine with guarded transitions** | `specification.md` → *Domain Model (diagram)*; *Task 2, 13*; *Edge E12*; *Verification (M5)* |
| **Optimistic concurrency control** (versioned aggregate) | `specification.md` → *Implementation Notes → Concurrency*; *Task 3*; *Edge E4* |
| **Deterministic, pure decision logic** (replayable/testable authZ) | `specification.md` → *Implementation Notes → Determinism*; *Task 10*; *Verification (M7 property test)* |
| **Data minimization + GDPR/CCPA rights** (export/erasure vs audit retention) | `specification.md` → *Privacy* |
| **No PII/PAN in logs or errors** | `specification.md` → *Privacy*; `agents.md` §5; `.claude/CLAUDE.md` Avoid |
| **Consistent typed error envelope + correct HTTP codes** | `specification.md` → *Implementation Notes → Error semantics*; *Task 14* |
| **Rate limiting + request-id tracing** | `specification.md` → *Performance (rate limit)*; *Task 15* |
| **SLOs as targets, not vibes** (latency percentiles, freshness, availability) | `specification.md` → *Expected Performance*; rationale above |
| **Access transparency** (auditing privileged/ops reads) | `specification.md` → *Task 12*; *Edge E11* |
| **Reconciliation against source-of-truth ledger** | `specification.md` → *Task 20*; *Verification (M4)* |
| **Quality gate for any implementation** (ruff/mypy/bandit/radon/coverage) | `agents.md` §1, §4; `.claude/CLAUDE.md` Definition of done |

---

<div align="center">

*Specification-driven design. Depth, goal-to-task traceability, and FinTech best practices are
the deliverable — no code required.*

</div>
