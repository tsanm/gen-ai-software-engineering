#!/usr/bin/env bash
# One-shot verification gate for the Homework 6 capstone.
#
# Runs the full quality gate (ruff, mypy, bandit, radon, pytest+coverage),
# executes the pipeline end-to-end, and checks structure/deliverables
# conformance against TASKS.md. Exits 0 only if everything passes.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

FAILED=0
section() { printf '\n=== %s ===\n' "$1"; }
check()   { if [[ $1 -eq 0 ]]; then echo "PASS: $2"; else echo "FAIL: $2"; FAILED=1; fi; }

section "Lint (ruff)"
$PY -m ruff check agents integrator.py mcp/server.py tests
check $? "ruff lint"

section "Format (ruff format --check)"
$PY -m ruff format --check agents integrator.py mcp/server.py
check $? "ruff format"

section "Types (mypy)"
$PY -m mypy agents integrator.py mcp/server.py
check $? "mypy"

section "Security (bandit, fail on >= medium)"
$PY -m bandit -q -r agents integrator.py mcp/server.py --severity-level medium
check $? "bandit (no medium/high)"

section "Complexity (radon, fail on C+)"
CC_OUT="$($PY -m radon cc -s -n C agents integrator.py mcp/server.py)"
if [[ -n "$CC_OUT" ]]; then echo "$CC_OUT"; check 1 "radon (no C+)"; else check 0 "radon (no C+)"; fi

section "Tests + coverage (>= 90%)"
$PY -m pytest --cov --cov-report=term-missing --cov-fail-under=90
check $? "pytest coverage >= 90%"

section "Pipeline end-to-end"
$PY integrator.py >/tmp/hw6_integrator_run.txt 2>&1
RC=$?
tail -n 5 /tmp/hw6_integrator_run.txt
check $RC "integrator runs to completion"

section "All transactions present in shared/results/"
$PY - <<'PYEOF'
import json, sys
from pathlib import Path
root = Path(".")
expected = {t["transaction_id"] for t in json.loads((root / "sample-transactions.json").read_text())}
results = {p.stem for p in (root / "shared" / "results").glob("*.json") if not p.name.startswith("_")}
missing = expected - results
sys.exit(0 if not missing else 1)
PYEOF
check $? "every transaction id appears in shared/results/"

section "TASKS deliverables / structure conformance"
conformance() { if [[ -e "$1" ]]; then echo "PASS: exists $1"; else echo "FAIL: missing $1"; FAILED=1; fi; }
conformance "specification.md"
conformance "agents.md"
conformance "CLAUDE.md"
conformance "agents-meta/spec-agent.agent.md"
conformance "agents-meta/code-agent.agent.md"
conformance "agents-meta/test-agent.agent.md"
conformance "agents-meta/doc-agent.agent.md"
conformance ".claude/commands/write-spec.md"
conformance ".claude/commands/run-pipeline.md"
conformance ".claude/commands/validate-transactions.md"
conformance ".claude/settings.json"
conformance "scripts/coverage_gate.sh"
conformance "scripts/pre_push_hook.py"
conformance "integrator.py"
conformance "agents/transaction_validator.py"
conformance "agents/fraud_detector.py"
conformance "agents/compliance_checker.py"
conformance "agents/settlement_processor.py"
conformance "agents/reporting_agent.py"
conformance "research-notes.md"
conformance "mcp.json"
conformance "mcp/server.py"
conformance "README.md"
conformance "HOWTORUN.md"
conformance "PLAN.md"
conformance "TEST_PLAN.md"
conformance "docs/screenshots/.gitkeep"
conformance "docs/screenshots/README.md"

section "Content conformance"
grep -q "Anton Tsiatsko" README.md; check $? "README contains author 'Anton Tsiatsko'"
grep -q "context7" mcp.json; check $? "mcp.json configures context7"
grep -q "pipeline-status" mcp.json; check $? "mcp.json configures pipeline-status"
grep -q "get_transaction_status" mcp/server.py; check $? "MCP exposes get_transaction_status"
grep -q "list_pipeline_results" mcp/server.py; check $? "MCP exposes list_pipeline_results"
grep -q "pipeline://summary" mcp/server.py; check $? "MCP exposes pipeline://summary resource"
grep -q "High-Level Objective" specification.md; check $? "spec has High-Level Objective"
grep -q "Low-Level Tasks" specification.md; check $? "spec has Low-Level Tasks"
grep -q "## Assumptions" specification.md; check $? "spec has Assumptions"
grep -q "## Traceability" specification.md; check $? "spec has Traceability"

section "Meta-agent definitions (agents-meta/)"
for f in agents-meta/spec-agent.agent.md agents-meta/code-agent.agent.md \
         agents-meta/test-agent.agent.md agents-meta/doc-agent.agent.md; do
  grep -q "^model:" "$f"; check $? "$f has model:"
  grep -q "YOU MUST" "$f"; check $? "$f has YOU MUST"
  grep -q "Self-Check" "$f"; check $? "$f has Self-Check"
  grep -q "REMEMBER" "$f"; check $? "$f has REMEMBER"
done

printf '\n========================================\n'
if [[ $FAILED -eq 0 ]]; then
  echo "VERIFY: ALL CHECKS PASSED"
  exit 0
else
  echo "VERIFY: FAILURES DETECTED"
  exit 1
fi
