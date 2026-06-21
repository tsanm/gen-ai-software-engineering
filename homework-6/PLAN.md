# Homework 6 — Capstone Build Plan

**Author:** Anton Tsiatsko

## Objective

Build four **meta-agents** (Specification, Code-generation, Unit-tests,
Documentation) whose output is a working **multi-agent banking transaction
processing pipeline**. The pipeline ingests `sample-transactions.json`, runs
each transaction through cooperating agents over a file-based JSON message bus,
and lands a final outcome per transaction in `shared/results/`.

## Architecture

```
sample-transactions.json
        │  (integrator seeds one envelope per txn into shared/input/)
        ▼
transaction_validator → fraud_detector → compliance_checker
        → settlement_processor → reporting_agent → shared/results/
```

* **File-based message bus**: `shared/{input,processing,output,results}`.
* **Standard envelope**: `message_id, timestamp(ISO-8601), source_agent,
  target_agent, message_type, data`.
* **Cross-cutting invariants** live in `agents/common.py`: `Decimal` money with
  `ROUND_HALF_UP`, ISO-4217 currency table, PII masking, audit logging.
* Rejected/held transactions short-circuit to the reporting agent so **every**
  input transaction reaches a terminal state.

## The four meta-agents (deliverables)

| Meta-agent | Produces | Plus |
|---|---|---|
| Agent 1 — Specification | `specification.md`, `agents.md` | skill `/write-spec` |
| Agent 2 — Code generation | `integrator.py`, `agents/*.py` | context7 (`research-notes.md`) |
| Agent 3 — Unit tests | `tests/*` + coverage gate | hook blocks push < 80% |
| Agent 4 — Documentation | `README.md`, `HOWTORUN.md` | author "Anton Tsiatsko" |

## Deliverables

* Spec: `specification.md`, `agents.md`, `.claude/commands/write-spec.md`.
* Pipeline: `integrator.py`, 5 agents under `agents/`, `research-notes.md`.
* Skills/hooks: `.claude/commands/{run-pipeline,validate-transactions}.md`,
  `.claude/settings.json` + `scripts/coverage_gate.sh` + `scripts/pre_push_hook.py`.
* MCP: `mcp.json` (context7 + pipeline-status), `mcp/server.py` (FastMCP).
* Tests/docs: `tests/`, `README.md`, `HOWTORUN.md`, `docs/screenshots/`.
* Verification: `verify.sh`, evidence under `docs/proofs/`.

## Low-level tasks (with Definition of Done)

| # | Task | DoD |
|---|---|---|
| 1 | `agents/common.py` infra | money/ISO-4217/masking/audit/message helpers; 100% covered |
| 2 | `transaction_validator.py` | field/amount/currency checks; `--dry-run`; radon < C |
| 3 | `fraud_detector.py` | explainable weighted score + band; thresholds tested |
| 4 | `compliance_checker.py` | blocklist + reporting threshold + hold logic |
| 5 | `settlement_processor.py` | Decimal fee/net with ROUND_HALF_UP; refunds handled |
| 6 | `reporting_agent.py` | per-txn finalize + run summary (json+text) |
| 7 | `integrator.py` | seeds input, runs chain in order, monitors completion |
| 8 | `mcp/server.py` | 2 tools + 1 resource; PII-safe; importable for tests |
| 9 | skills + hook | 3 slash commands; push-gate blocks < 80% |
| 10 | tests | unit per agent + integration via tmp_path; coverage ≥ 90% |
| 11 | docs | README (author, diagram, tech table), HOWTORUN, research-notes |
| 12 | verify | `verify.sh` exits 0; proofs captured to `docs/proofs/` |

## Quality bar

`ruff` + `mypy --strict` + `bandit` (no medium/high) + `radon` (no C+) +
`pytest --cov` ≥ 90% (gate floor 80%). All enforced by `verify.sh`.
