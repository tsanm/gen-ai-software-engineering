# CLAUDE.md — Homework 4 (4-Agent Bug-Fix Pipeline)

Project rules for this agentic pipeline. The build plan is [`PLAN.md`](PLAN.md); the verification
contract is [`TEST_PLAN.md`](TEST_PLAN.md). On any conflict, those win.

## What this is
A single-command, **sequential** multi-agent pipeline (Architect/Editor pattern) that fixes seeded
bugs in the `paycli` app, security-reviews the changes, and generates FIRST unit tests — capturing
every run in an immutable, timestamped folder.

## Golden rules (never violate)
- **Single responsibility per agent.** Architect agents (research, verify, RCA, plan, security) are
  **read-only → Opus**; Editor agents (fix, tests) **write → Sonnet**.
- **Report-only means read-only.** The security-verifier never edits code (enforced by tool scope).
- **Fail on test failure.** The bug-fixer stops and documents if a change breaks tests; it reflects
  on the failure and retries before continuing.
- **No secrets in committed code.** The seeded secret is remediated to an env var.
- **Structured file handoffs + immutability.** Each stage writes one artifact ending in a
  `## Handoff → next` section; never mutate a prior stage's output; each run gets a **new** folder.
- **Human checkpoints** before planning (review `verified-rca.md`) and before implementation
  (review `implementation-plan.md`).

## Run
`./run-pipeline.sh` (macOS/Linux) or `pwsh ./run-pipeline.ps1` (Windows). See [`HOWTORUN.md`](HOWTORUN.md).

## Quality gate (all green to ship)
`ruff` · `mypy` · `bandit` (no HIGH) · `radon` (no C-or-worse) · `pytest` with coverage **≥ 90%** on
`src/paycli/`.
