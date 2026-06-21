# How to Run — Homework 6 Multi-Agent Banking Pipeline

**Author:** Anton Tsiatsko

Follow these numbered steps from a clean checkout.

## 1. Prerequisites

- Python 3.11+ (`python3 --version`)
- Node.js + `npx` (only for the context7 MCP server)

## 2. Set up the environment

```bash
cd homework-6
python3 -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## 3. Run the pipeline

```bash
python integrator.py
```

Expected: an audit line per agent per transaction, then a **Pipeline Run
Summary**, and finally `OK: all 8 transactions appear in shared/results/`.
Per-transaction outcomes are in `shared/results/<TXN>.json`; the roll-up is in
`shared/results/_summary.{json,txt}`.

> Screenshot this terminal output → `docs/screenshots/pipeline-run.png`.

## 4. Validate transactions only (dry run)

```bash
python agents/transaction_validator.py --dry-run
```

Prints total / valid / invalid counts and a per-transaction reason table — no
fraud/compliance/settlement is performed.

## 5. Run the tests with coverage

```bash
python -m pytest --cov --cov-report=term-missing
```

Expected: all tests pass with total coverage ≥ 90%.

> Screenshot the coverage report → `docs/screenshots/test-coverage.png`.

## 6. Run the full verification gate

```bash
bash verify.sh
```

Runs ruff, mypy, bandit, radon, pytest+coverage (≥ 90%), the pipeline, and the
TASKS structure/deliverables conformance checks. Exits `0` only if everything
passes. A captured run is in `docs/proofs/`.

## 7. Use the Claude Code skills (slash commands)

In Claude Code, from the repo root:

- `/write-spec` — (re)generate `specification.md` from the template (Agent 1).
- `/run-pipeline` — run the pipeline end-to-end and summarise results.
- `/validate-transactions` — dry-run validation only.

> Screenshot `/run-pipeline` executing → `docs/screenshots/skill-run-pipeline.png`.

## 8. See the coverage-gate hook block a push

The hook in `.claude/settings.json` runs `scripts/pre_push_hook.py` before any
Bash command and **denies** `git push` if coverage is below 80%.

Demo the deny path (temporarily raise the threshold so it cannot be met):

```bash
sed 's/THRESHOLD = 80/THRESHOLD = 100/' scripts/pre_push_hook.py > /tmp/hook100.py
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin x"}}' \
  | python /tmp/hook100.py
# -> {"hookSpecificOutput": {... "permissionDecision": "deny" ...}}
```

The real (80%) gate allows the push because coverage is ~99%.

> Screenshot the hook firing → `docs/screenshots/hook-trigger.png`.

## 9. Use the MCP servers

`mcp.json` configures two servers:

- **context7** — `npx -y @upstash/context7-mcp@latest` (library doc lookups).
- **pipeline-status** — `python mcp/server.py` (custom FastMCP server).

Start the custom server standalone:

```bash
python mcp/server.py
```

It exposes the tools `get_transaction_status(transaction_id)` and
`list_pipeline_results()`, plus the resource `pipeline://summary`. (Run the
pipeline first so `shared/results/` is populated.)

> Screenshot a context7 query **and** a custom MCP tool call →
> `docs/screenshots/mcp-interaction.png`.
