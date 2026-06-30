# HOWTORUN — Homework 4 (4-Agent Bug-Fix Pipeline)

## Prerequisites
- **Python 3.11+**
- **Claude Code CLI** (`claude`) installed and authenticated (the pipeline drives agents via `claude -p`).

## 1. Set up the app environment
```bash
cd homework-4
python3 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
```

## 2. (Optional) see the bugs BEFORE the fix
```bash
./.venv/bin/python -m pytest tests/    # baseline fails on BUG-A (boundary) and BUG-B (empty)
./.venv/bin/bandit -r src              # flags VULN-1 (subprocess shell=True, B602 HIGH)
```

## 3. Run the pipeline (single command)
```bash
./run-pipeline.sh                      # macOS/Linux
# pwsh ./run-pipeline.ps1              # Windows
# AUTO_APPROVE=0 ./run-pipeline.sh     # pause for human approval at the 2 checkpoints
```
Each run creates a new immutable folder `context/bugs/001/runs/run-<UTC>/` with one
`NN-agent_log.md` + `NN-agent_result.md` per stage, `04-CHECKPOINT-1.md`, `06-CHECKPOINT-2.md`,
`manifest.json`, and `pipeline-run.log`. The latest results are copied to the canonical artifacts in
`context/bugs/001/` (`codebase-research.md`, `verified-research.md`, `rca.md`, `verified-rca.md`,
`implementation-plan.md`, `fix-summary.md`, `security-report.md`, `test-report.md`).

## 4. Verify it worked (AFTER the fix)
```bash
./.venv/bin/python -m pytest --cov=paycli   # all green; coverage ≥ 90%
./.venv/bin/bandit -r src                   # clean (no HIGH/CRITICAL)
./verify.sh                                 # runs the TEST_PLAN checks end-to-end
```

## 5. Inspect a run (one folder, execution order)
```bash
ls context/bugs/001/runs/run-*/             # whole pipeline in order (checkpoints in position)
cat context/bugs/001/runs/run-*/*_result.md # replay every stage result top-to-bottom
```
