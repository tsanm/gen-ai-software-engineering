# Homework 6 — Test Plan

**Author:** Anton Tsiatsko

Priorities: **P0** = must pass for the submission to be acceptable; **P1** =
quality/robustness. Every check is automated (run via `pytest` and/or
`verify.sh`) unless explicitly marked manual.

## P0 — Functional correctness

| ID | Check | How verified |
|---|---|---|
| P0-1 | Money uses `Decimal`; `float` amounts rejected | `test_common::test_parse_money_rejects_float`, exactness test |
| P0-2 | `ROUND_HALF_UP` quantisation per ISO-4217 minor units | `test_common::test_quantize_money_*` (USD, EUR, JPY) |
| P0-3 | Validator rejects missing fields / bad currency / bad amount | `test_transaction_validator.py` |
| P0-4 | Refund negative amounts allowed; transfers not | `test_transaction_validator` refund tests |
| P0-5 | Fraud scoring bands + thresholds (high-value, off-hours, cross-border, wire) | `test_fraud_detector.py` |
| P0-6 | Compliance blocklist + reporting threshold + hold-on-fraud | `test_compliance_checker.py` |
| P0-7 | Settlement Decimal fee/net, refunds, held/rejected passthrough | `test_settlement_processor.py` |
| P0-8 | Reporting builds correct summary (counts, totals, flags) | `test_reporting_agent.py` |
| P0-9 | Full pipeline: every input txn appears in `shared/results/` | `test_integration::test_full_pipeline_*`, `verify.sh` |
| P0-10 | Each agent uses `process_message(message: dict) -> dict` and routes correctly | per-agent `test_process_message_*` |
| P0-11 | Result files are valid standard message envelopes | `test_integration::test_message_protocol_shape` |
| P0-12 | MCP tools `get_transaction_status`, `list_pipeline_results`, resource `pipeline://summary` | `test_mcp_server.py` |
| P0-13 | Coverage gate blocks push when coverage < 80% | manual + `scripts/pre_push_hook.py` deny-path demo |

## P1 — Security, isolation, robustness

| ID | Check | How verified |
|---|---|---|
| P1-1 | No plaintext PII (account numbers) in audit log | `test_integration::test_results_are_pii_safe` |
| P1-2 | MCP responses mask account numbers | `test_mcp_server::test_get_transaction_status_found` |
| P1-3 | Tests isolated from real `shared/` via `tmp_path` | all integration/MCP tests use `tmp_path` fixtures |
| P1-4 | Audit logger is idempotent (no handler stacking) | `test_common::test_configure_audit_logger_idempotent` |
| P1-5 | Bad/empty inputs handled gracefully | invalid-amount, bad-timestamp, missing-summary tests |
| P1-6 | Coverage ≥ 90% (gate floor 80%) | `pytest --cov-fail-under=90` in `verify.sh` |

## Quality gate (enforced by `verify.sh`)

| Tool | Pass condition |
|---|---|
| `ruff check` | no lint errors |
| `ruff format --check` | already formatted |
| `mypy` (strict) | no type errors |
| `bandit` | no medium/high findings |
| `radon cc` | no function graded C or worse |
| `pytest --cov` | all tests pass, coverage ≥ 90% |

## TASKS structure / deliverables conformance

`verify.sh` asserts the presence of every required file and key content
markers:

- SSOT docs: `specification.md` (High-Level Objective + Low-Level Tasks +
  `## Assumptions` + `## Traceability`), `agents.md`, `CLAUDE.md`,
  `.claude/commands/write-spec.md`.
- Meta-agents: `agents-meta/{spec,code,test,doc}-agent.agent.md`, each asserted
  to contain `model:`, `YOU MUST`, `Self-Check`, and `REMEMBER`.
- Pipeline: `integrator.py`, `agents/{transaction_validator,fraud_detector,
  compliance_checker,settlement_processor,reporting_agent}.py`, `research-notes.md`.
- Skills/hooks: `.claude/commands/{run-pipeline,validate-transactions}.md`,
  `.claude/settings.json`, `scripts/coverage_gate.sh`, `scripts/pre_push_hook.py`.
- MCP: `mcp.json` (context7 + pipeline-status), `mcp/server.py` (2 tools + resource).
- Docs: `README.md` (author "Anton Tsiatsko" + ASCII diagram + tech table),
  `HOWTORUN.md`, `docs/screenshots/` (`.gitkeep` + capture index).

## Manual checks (for the author, captured as screenshots)

| Screenshot | Validates |
|---|---|
| `pipeline-run.png` | P0-9 pipeline completes |
| `test-coverage.png` | P1-6 coverage ≥ 80/90% |
| `skill-run-pipeline.png` | `/run-pipeline` skill executes |
| `hook-trigger.png` | P0-13 coverage gate hook fires |
| `mcp-interaction.png` | P0-12 context7 + custom MCP tool call |
