# agents.md — Operating Contract for AI Agents (Homework 6)

**Author:** Anton Tsiatsko · **Project:** Multi-Agent Banking Transaction Pipeline

This is the behavioural contract for any AI coding agent working in this repo
(Claude Code, Copilot, etc.). It defines HOW to work; `specification.md` defines
WHAT to build (the authoritative numbers); `CLAUDE.md` is the always-on subset.
**Reference `specification.md` for exact thresholds/fees/currencies — do not
duplicate those numbers here.**

## What this project is

A multi-agent banking **transaction processing pipeline**. Five cooperating
runtime agents pass JSON messages through a file-based bus (`shared/`) to
validate, risk-score, compliance-screen, settle and report on transactions
loaded from `sample-transactions.json`. The whole system is the output of four
**meta-agents** — Specification, Code-generation, Unit-tests, Documentation —
defined in `agents-meta/*.agent.md`.

## Repository map

```
homework-6/
├── CLAUDE.md                 # always-on rules (SSOT subset)
├── specification.md          # WHAT to build (authoritative numbers)
├── agents.md                 # this file — HOW agents behave
├── agents-meta/              # the four meta-agent definitions (.agent.md)
├── integrator.py             # orchestrator: seeds input, runs the chain
├── agents/                   # runtime agents + common.py (money/ISO/mask/audit/envelope)
├── mcp/server.py             # FastMCP pipeline-status server
├── mcp.json                  # context7 + pipeline-status MCP config
├── scripts/                  # coverage_gate.sh, pre_push_hook.py
├── tests/                    # unit + integration tests (tmp_path isolated)
├── .claude/commands/         # /write-spec, /run-pipeline, /validate-transactions
├── .claude/settings.json     # coverage-gate hook (blocks push < 80%)
└── shared/                   # input | processing | output | results (runtime)
```

## Tech stack & quality gate

- **Language:** Python 3.11+. **Money:** `decimal.Decimal` + `ROUND_HALF_UP`.
- **Messaging:** file-based JSON envelopes over `shared/`.
- **MCP:** FastMCP custom server (`pipeline-status`) + external `context7`.
- **Gate (enforced by `verify.sh`):** ruff lint+format · mypy strict · bandit
  (no medium/high) · radon (no function graded C+) · pytest with coverage.
  Coverage **gate floor is 80%** (push blocked below); the suite targets ≥ 90%.
  The authoritative coverage numbers live in `specification.md`.

## Workflow (plan → act → verify)

1. **Read first.** Read `CLAUDE.md`, `specification.md` (for the numbers), and
   the file(s) you will touch. Closed-world: if a field/threshold/code is not in
   the spec, **ask — do not guess**.
2. **Plan, then act.** State the change and the files it touches before editing.
   Keep planning and editing separate.
3. **Implement** against the uniform agent contract:
   `process_message(message: dict) -> dict` returning a standard envelope.
4. **Test** the changed behaviour (unit + integration), isolated via `tmp_path`.
5. **Verify** with `bash verify.sh` and `.venv/bin/python -m pytest -q`. Both
   must be green before you are done.

## Message envelope (standard)

```json
{
  "message_id": "uuid4-string",
  "timestamp": "2026-03-16T10:00:00Z",
  "source_agent": "transaction_validator",
  "target_agent": "fraud_detector",
  "message_type": "transaction",
  "data": { "transaction_id": "TXN001", "amount": "1500.00", "currency": "USD" }
}
```

## Non-negotiables

- **Money:** `decimal.Decimal` only, parsed from strings, quantised
  `ROUND_HALF_UP` to the currency's minor units. Never `float`. (Numbers: spec §3.)
- **Security / PII:** mask account numbers and descriptions before logging or
  returning over MCP. No plaintext PII ever reaches a log line or a response.
- **Audit:** one line per operation — ISO-8601 timestamp, agent, transaction id,
  outcome (masked detail only).
- **Anti-hallucination:** ground every claim in `file:line` (verify by reading,
  not memory); cite the spec for numbers; never invent APIs/fields/codes.
- **Closed-world:** the spec is the only source of endpoints, fields, currencies
  and codes. Unknown ⇒ reject (fail closed) or ask — never invent.

## What never to do

- Never use `float` for money or skip `ROUND_HALF_UP`.
- Never log / return raw account numbers or descriptions.
- Never invent endpoints, fields, currencies, or codes not in `specification.md`.
- Never weaken a test or assertion to force a pass; never leave tests red.
- Never write to the real `shared/` from tests.
- Never change pipeline logic or test intent during a docs/agent-enrichment task.

## When extending

Add a new agent: implement `process_message`, register it in
`integrator.STAGE_ORDER`/`STAGE_FUNCS`, add unit tests, keep functions below
radon grade C, and update `specification.md` + this file.
