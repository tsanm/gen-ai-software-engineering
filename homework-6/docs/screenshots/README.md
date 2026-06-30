# Screenshots (Author: Anton Tsiatsko)

The five required captures, all taken on the author's machine after running the
steps in `../../HOWTORUN.md` (nothing fabricated). They are also embedded in the
PR #6 description.

| File | What it shows | Source |
|---|---|---|
| `pipeline-run.png` | Pipeline run as a visual status board — agent flow, 8-transaction table, settled/held/rejected stats, per-currency totals, links to results/agents/PR | `render-status.py` (HW4-style board), HOWTORUN §3 |
| `test-coverage.png` | `pytest --cov` report — `TOTAL 99%`, 78 passed (gate floor 80%) | HOWTORUN §5 |
| `skill-run-pipeline.png` | The `/run-pipeline` skill executing in Claude Code with its result summary | HOWTORUN §7 |
| `hook-trigger.png` | Coverage-gate hook intercepting `git push` — DENY at 100% / ALLOW at 80%, real 99% coverage | `scripts/demo_hook.py`, HOWTORUN §8 |
| `mcp-interaction.png` | Real calls to both MCP servers — context7 doc lookup **and** custom `get_transaction_status` / `list_pipeline_results` (PII-masked) | HOWTORUN §9 |
