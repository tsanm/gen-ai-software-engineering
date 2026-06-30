#!/usr/bin/env bash
# Coverage gate: runs the test-suite with coverage and FAILS (non-zero exit)
# if total line coverage is below the threshold. Wired into the Claude Code
# PreToolUse hook (see .claude/settings.json) so `git push` is blocked when
# coverage regresses below 80%.
#
# Usage: scripts/coverage_gate.sh [threshold]
set -euo pipefail

THRESHOLD="${1:-80}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# Prefer the project venv if present, else fall back to the active interpreter.
if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

echo "[coverage-gate] threshold=${THRESHOLD}% interpreter=${PY}"

# --cov-fail-under makes pytest exit non-zero when coverage < threshold.
set +e
"$PY" -m pytest --cov --cov-report=term-missing "--cov-fail-under=${THRESHOLD}"
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]]; then
  echo "[coverage-gate] BLOCKED: coverage is below ${THRESHOLD}% (or tests failed)." >&2
  exit 1
fi

echo "[coverage-gate] PASS: coverage >= ${THRESHOLD}%."
