# Project Context for AI Agents (`agents.md`)

**Author:** Anton Tsiatsko · **Project:** Homework 6 — Multi-Agent Banking Pipeline

This file gives any AI coding agent (Claude Code, Copilot, etc.) the context it
needs to work in this repository correctly and safely.

## What this project is

A multi-agent banking **transaction processing pipeline**. Five cooperating
agents pass JSON messages through a file-based bus (`shared/`) to validate,
risk-score, compliance-screen, settle and report on transactions loaded from
`sample-transactions.json`. It is the output of four **meta-agents**
(Specification, Code-generation, Unit-tests, Documentation).

## Repository map

```
homework-6/
├── integrator.py            # orchestrator: seeds input, runs the chain
├── agents/
│   ├── common.py            # money, ISO-4217, masking, audit, Message envelope
│   ├── transaction_validator.py
│   ├── fraud_detector.py
│   ├── compliance_checker.py
│   ├── settlement_processor.py
│   └── reporting_agent.py
├── mcp/server.py            # FastMCP pipeline-status server
├── mcp.json                 # context7 + pipeline-status MCP config
├── scripts/                 # coverage_gate.sh, pre_push_hook.py
├── tests/                   # unit + integration tests (tmp_path isolated)
├── .claude/commands/        # /write-spec, /run-pipeline, /validate-transactions
├── .claude/settings.json    # coverage-gate hook (blocks push < 80%)
└── shared/                  # input | processing | output | results (runtime)
```

## Non-negotiable engineering rules

1. **Money is `decimal.Decimal`.** Never use `float` for amounts. Parse from
   strings; quantise with `ROUND_HALF_UP` to the currency's minor units
   (`agents.common.parse_money` / `quantize_money`).
2. **ISO-4217 only.** Validate currency against `SUPPORTED_CURRENCIES`.
3. **No plaintext PII.** Mask account numbers and descriptions before logging
   (`mask_account`, `mask_text`). Audit lines carry masked values only.
4. **Audit everything.** One line per agent operation: ISO-8601 timestamp,
   agent, transaction id, outcome.
5. **Uniform agent contract.** Each agent exposes
   `process_message(message: dict) -> dict` and returns a standard envelope.
6. **Tests stay isolated.** Use `tmp_path`; never write to the real `shared/`.

## Message envelope

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

## How to run / verify

- Pipeline: `python integrator.py` (or `/run-pipeline`).
- Validate only: `python agents/transaction_validator.py --dry-run`.
- Full gate: `bash verify.sh` (ruff, mypy, bandit, radon, pytest+coverage,
  pipeline, conformance).

## When extending

- Add a new agent: implement `process_message`, register it in
  `integrator.STAGE_ORDER`/`STAGE_FUNCS`, add unit tests, keep functions below
  radon grade C, and update this file + `specification.md`.
