# CLAUDE.md — Always-On Project Rules (Homework 6)

**Author:** Anton Tsiatsko · **Project:** Multi-Agent Banking Transaction Pipeline

This file is the always-loaded subset of the project's single source of truth (SSOT).
Read it before every change.

## SSOT trio (no duplication — link, don't copy)
- **`specification.md`** = WHAT to build (objectives, low-level tasks, exact numbers). Authoritative for thresholds, fees, currencies, fields.
- **`agents.md`** = HOW agents behave (operating contract, workflow, non-negotiables).
- **`CLAUDE.md`** (this file) = the always-on subset of those rules.
- The four meta-agent definitions live in **`agents-meta/*.agent.md`**.

## Golden rules (non-negotiable)
1. **Money = `decimal.Decimal`** — never `float`. Parse from strings; quantise `ROUND_HALF_UP` to the currency's minor units (`agents.common.parse_money` / `quantize_money`).
2. **Currency = ISO-4217 only** — validate against `SUPPORTED_CURRENCIES`; reject unknown codes.
3. **No plaintext PII** — mask account numbers and descriptions before logging or returning over MCP (`mask_account`, `mask_text`).
4. **Audit everything** — one line per agent operation: ISO-8601 timestamp + agent name + transaction id + outcome (masked detail only).
5. **File-based JSON bus + standard envelope** — agents communicate via `shared/{input,processing,output,results}`; every message uses the standard envelope (see `agents.md`).
6. **Fail closed on validation** — when an input is missing, malformed, or unverifiable, reject with a human-readable `reason`; never pass dirty data downstream.
7. **Coverage gate ≥ 80%** — push is blocked below 80% (`scripts/pre_push_hook.py`); aim ≥ 90%.

## Conventions
- Uniform agent contract: `process_message(message: dict) -> dict` returning a standard envelope.
- Tests isolate from the real `shared/` via `tmp_path`; one behaviour per test, deterministic.
- Quality gate: ruff (lint+format), mypy (strict), bandit (no medium/high), radon (no C+).
- Exact numbers (thresholds, fee rate, currencies, off-hours window) live in `specification.md` — reference them, do not re-state them here.

## Never
- Never use `float` for money, or skip `ROUND_HALF_UP` quantisation.
- Never log or return raw account numbers / descriptions.
- Never invent endpoints, fields, currencies, or codes not in `specification.md` (closed-world; ask-don't-guess).
- Never weaken a test or assertion to make the suite pass.
- Never write to the real `shared/` from tests.
- Never change pipeline logic or test intent for a docs/agent-enrichment task.

## Run
```bash
cd homework-6
bash verify.sh                 # full quality + conformance gate
.venv/bin/python -m pytest -q  # tests only
.venv/bin/python integrator.py # run the pipeline (or /run-pipeline)
```
