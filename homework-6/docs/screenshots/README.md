# Screenshots to Capture (Author: Anton Tsiatsko)

Capture these five screenshots and place them in this folder. They must also be
embedded/linked in the PR description. **Do not fabricate screenshots** — take
them from your own machine after running the steps in `../../HOWTORUN.md`.

| File | What to capture | How (see HOWTORUN.md step) |
|---|---|---|
| `pipeline-run.png` | Full terminal output of `python integrator.py` ending in "OK: all 8 transactions appear in shared/results/" | Step 3 |
| `test-coverage.png` | `pytest --cov` report showing total coverage ≥ 80% (ideally ≥ 90%) | Step 5 |
| `skill-run-pipeline.png` | The `/run-pipeline` slash command executing inside Claude Code | Step 7 |
| `hook-trigger.png` | The coverage-gate hook firing / blocking a `git push` (deny decision) | Step 8 |
| `mcp-interaction.png` | A context7 query result **and** a custom MCP tool call (e.g. `get_transaction_status` or `list_pipeline_results`) | Step 9 |

Tip: a single wide terminal screenshot can cover both halves of
`mcp-interaction.png` (context7 result on top, custom tool call below).
