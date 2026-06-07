#!/usr/bin/env bash
# Run the full code-quality gate (the local "SonarQube-equivalent" stack).
# Usage: ./demo/quality.sh   (run from the homework-1 directory)
set -euo pipefail
cd "$(dirname "$0")/.."

PY="./.venv/bin/python"
[ -d ".venv" ] || python3 -m venv .venv
$PY -m pip install --quiet -r requirements-dev.txt

echo "▶ ruff (lint + import order)"
$PY -m ruff check src tests

echo "▶ mypy (static type check)"
$PY -m mypy src

echo "▶ bandit (security static analysis)"
$PY -m bandit -rq src

echo "▶ radon (cyclomatic complexity, fail on any C+ block)"
if $PY -m radon cc src -nc -s | grep -E "[C-F] \("; then
  echo "✗ complexity too high (C or worse)"; exit 1
fi
$PY -m radon cc src -a -s | tail -1

echo "▶ pytest + coverage (fail under 95%)"
$PY -m pytest --cov=src --cov-report=term-missing

echo "✅ All quality checks passed."
