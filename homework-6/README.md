# Homework 6 — AI-Powered Multi-Agent Banking Pipeline

**Created by Anton Tsiatsko**

A final-capstone project in which four **meta-agents** (Specification,
Code-generation, Unit-tests, Documentation) build and verify a working
**multi-agent banking transaction processing pipeline**.

## What this system does

The pipeline ingests raw banking transactions from `sample-transactions.json`
and drives each one through five cooperating agents that communicate over a
**file-based JSON message bus** (`shared/{input,processing,output,results}`).
Each transaction is validated, risk-scored for fraud, screened for compliance,
settled (with precise `Decimal` money math), and finally reported — landing a
terminal outcome in `shared/results/` together with a run-summary report.

Engineering invariants are enforced everywhere: monetary amounts use
`decimal.Decimal` with `ROUND_HALF_UP` (never `float`), currencies are checked
against ISO 4217, every operation is written to a structured audit log with an
ISO-8601 timestamp, and account numbers are **masked** so no plaintext PII ever
reaches a log line or an MCP response.

## Agents

- **Transaction Validator** — checks required fields, non-zero/valid amounts
  (negatives only for refunds), and supported ISO-4217 currency; normalises the
  amount to the currency's minor units.
- **Fraud Detector** — assigns an explainable `risk_score` (high-value bands,
  off-hours timing, cross-border, wire-transfer rail) and flags high risk for
  review.
- **Compliance Checker** — rejects blocked-account transactions, raises a
  regulatory-report flag at ≥ 10,000, and holds fraud-flagged transactions.
- **Settlement Processor** — settles approved transactions with a `Decimal`
  fee and net amount (ROUND_HALF_UP); passes held/rejected through unchanged.
- **Reporting Agent** — finalises each record into `shared/results/` and builds
  the run summary (counts by status, settled totals per currency, flagged and
  rejected lists).
- **Integrator** (orchestrator) — sets up `shared/`, seeds input, runs the
  chain in order, and confirms every transaction reached `shared/results/`.

## Architecture

```
                         sample-transactions.json
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    integrator     │  seeds one JSON envelope
                         │  (orchestrator)   │  per txn into shared/input/
                         └─────────┬─────────┘
                                   │
          shared/ message bus:  input → processing → output → results
                                   │
     ┌─────────────┐   ┌────────────────┐   ┌──────────────────┐
     │ transaction │──▶│     fraud      │──▶│   compliance     │
     │  validator  │   │   detector     │   │    checker       │
     └──────┬──────┘   └────────────────┘   └────────┬─────────┘
            │ rejected                                │ approved
            │                          held/rejected  │
            ▼                                          ▼
     ┌──────────────┐                       ┌────────────────────┐
     │  reporting   │◀──────────────────────│    settlement      │
     │    agent     │     settled records   │    processor       │
     └──────┬───────┘                       └────────────────────┘
            │
            ▼
     shared/results/<TXN>.json   +   shared/results/_summary.{json,txt}
                                   │
                                   ▼
                    MCP pipeline-status server (mcp/server.py)
        get_transaction_status · list_pipeline_results · pipeline://summary
```

Rejected transactions (e.g. unsupported currency, blocked account) and held
transactions (fraud review) short-circuit straight to the reporting agent, so
**every** input transaction reaches a terminal state in `shared/results/`.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | typed, batteries-included stdlib |
| Money | `decimal.Decimal` + ROUND_HALF_UP | exact banking arithmetic, no float error |
| Messaging | File-based JSON envelopes | simple, inspectable inter-agent bus |
| MCP server | FastMCP (`fastmcp`) | exposes pipeline state as tools + a resource |
| MCP (external) | context7 | library doc lookups during code generation |
| Tests | pytest + pytest-cov | unit + integration, coverage ≥ 90% |
| Lint / format | ruff | fast lint + formatter |
| Types | mypy (strict) | static type safety |
| Security | bandit | static security scan (no medium/high) |
| Complexity | radon | enforce no function graded C+ |
| Automation | Claude Code skills + hook | `/run-pipeline`, push coverage gate |

## The four meta-agents

The system is built by four meta-agents, each defined as a proper agent in
`agents-meta/` (WORK-Agents structure: role, `YOU MUST` / `YOU MUST NOT`,
process with output schemas, self-check, error handling, mantra):

- [`agents-meta/spec-agent.agent.md`](agents-meta/spec-agent.agent.md) — Specification
- [`agents-meta/code-agent.agent.md`](agents-meta/code-agent.agent.md) — Code generation
- [`agents-meta/test-agent.agent.md`](agents-meta/test-agent.agent.md) — Unit tests
- [`agents-meta/doc-agent.agent.md`](agents-meta/doc-agent.agent.md) — Documentation

## Deliverables → TASKS coverage

| Meta-agent (definition) | TASKS | Deliverables |
|---|---|---|
| `agents-meta/spec-agent.agent.md` (Agent 1 — Specification) | Task 1 | `specification.md`, `agents.md`, `CLAUDE.md`, `/write-spec` skill |
| `agents-meta/code-agent.agent.md` (Agent 2 — Code generation) | Tasks 2, 4 | `integrator.py`, `agents/*.py`, `mcp/server.py`, `mcp.json`, `research-notes.md` (context7) |
| `agents-meta/test-agent.agent.md` (Agent 3 — Unit tests) | Tasks 3, 5 | `tests/`, `/run-pipeline` + `/validate-transactions` skills, coverage gate hook (blocks push < 80%) |
| `agents-meta/doc-agent.agent.md` (Agent 4 — Documentation) | Task 5 | this `README.md`, `HOWTORUN.md`, `docs/screenshots/` |

The SSOT docs (`CLAUDE.md` = always-on rules, `specification.md` = what,
`agents.md` = behaviour) keep all four meta-agents working against one source of
truth.

## Industry / cross-homework best-practices mapping

This capstone consolidates the strongest practices from the earlier homeworks so
every cross-cutting dimension is covered in one place.

| Best practice | Where it appears here | Lineage |
|---|---|---|
| Quality gate (ruff + mypy strict + bandit + radon + coverage) | `verify.sh`, `pyproject.toml` | HW2 |
| Coverage floor enforced on push | `scripts/pre_push_hook.py` + `coverage_floor` in `pipeline.config.json` | HW2/HW4 |
| TDD breadth: unit-per-agent + integration via `tmp_path` | `tests/` | HW2 |
| Convenience run script | `python integrator.py`, `/run-pipeline` skill | HW2 `demo/` |
| Layered specification (Authority/closed-world, NFR, Implementation Notes, Assumptions) | `specification.md` | HW3 |
| **Worked Example** (one txn end to end) | `specification.md` §3a | HW3 |
| **Outcome & Reason Catalog** (stable codes) | `specification.md` §3b | HW3 (Error Code Catalog) |
| Traceability matrix (agent → deliverable → test) | `specification.md` §Traceability | HW3 |
| SSOT doc trio (spec / behaviour / always-on rules) | `specification.md`, `agents.md`, `CLAUDE.md` | HW3 |
| Best-practices mapping table | this table | HW3 |
| Agent definitions with role/MUST/Self-Check | `agents-meta/*.agent.md` | HW4 (WORK-Agents) |
| **Config-driven engine** (order, thresholds, paths) | `pipeline.config.json` (read by `integrator.py` + agents) | HW4 |
| **Immutable timestamped run folders** + per-run audit log + manifest | `shared/runs/run-<UTC>/` (see `capture_run`) | HW4 |
| `verify.sh` conformance gate + `docs/proofs/` evidence | `verify.sh`, `docs/proofs/` | HW4 |
| PLAN.md + TEST_PLAN.md with P0/P1 checks | `PLAN.md`, `TEST_PLAN.md` | HW4 |

## Quick start

```bash
cd homework-6
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python integrator.py          # run the pipeline
bash verify.sh                # run the full quality + conformance gate
```

See **[HOWTORUN.md](HOWTORUN.md)** for step-by-step instructions and the MCP /
skills / hook demos. Screenshots to embed live in `docs/screenshots/`.
