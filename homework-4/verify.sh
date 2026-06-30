#!/usr/bin/env bash
# verify.sh — runs the scriptable TEST_PLAN checks for Homework 4.
# Exit 0 only if every P0 check passes. Run AFTER the pipeline completes.
set -uo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
BUG="context/bugs/001"
RUN="$(ls -dt "$BUG"/runs/run-* 2>/dev/null | head -1)"
pass=0; fail=0
ok(){ echo "  PASS  $1"; pass=$((pass+1)); }
no(){ echo "  FAIL  $1"; fail=$((fail+1)); }
chk(){ local d="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$d"; else no "$d"; fi; }
has(){ [ -s "$1" ]; }                       # file present + non-empty
grep_q(){ grep -qE "$1" "$2" 2>/dev/null; }

echo "== Engineering quality gate =="
chk "ruff clean"                 $PY -m ruff check src tests
chk "mypy clean"                 $PY -m mypy src
chk "radon: no C-or-worse"       bash -c "[ -z \"\$($PY -m radon cc -n C src)\" ]"
chk "bandit: no HIGH/CRITICAL"   bash -c "$PY -m bandit -r src -lll -q | grep -q 'No issues identified' || ! $PY -m bandit -r src -lll -q 2>/dev/null | grep -qiE 'Severity: High|Severity: Critical'"
chk "pytest green, coverage >=90% on src/paycli" $PY -m pytest --cov=paycli --cov-fail-under=90

echo "== Canonical artifacts (9) =="
for f in research/codebase-research.md research/verified-research.md rca.md verified-rca.md \
         implementation-plan.md fix-summary.md security-report.md test-report.md bug-context.md; do
  chk "artifact $f" has "$BUG/$f"
done

echo "== Run capture =="
chk "run folder exists"          test -d "$RUN"
chk "manifest.json present"      has "$RUN/manifest.json"
chk "CHECKPOINT-1 recorded"      has "$RUN/04-CHECKPOINT-1.md"
chk "CHECKPOINT-2 recorded"      has "$RUN/06-CHECKPOINT-2.md"
chk "8 stages have log+result"   bash -c "[ \$(ls \"$RUN\"/0*_log.md 2>/dev/null | wc -l) -eq 8 ] && [ \$(ls \"$RUN\"/0*_result.md 2>/dev/null | wc -l) -eq 8 ]"
chk "handoff in stage results"   bash -c "grep -lq Handoff \"$RUN\"/00-bug-researcher_result.md"

echo "== Fix correctness (post-fix source) =="
chk "BUG-A fixed (<= used, no strict < limit)" bash -c "grep -q 'spent + amount <= limit' src/paycli/transactions.py"
chk "BUG-B fixed (empty guard)"  bash -c "grep -qE 'if not amounts|len\(amounts\) == 0|return 0' src/paycli/transactions.py"
chk "VULN-1 fixed (no shell=True)" bash -c "! grep -q 'shell=True' src/paycli/report.py"
chk "VULN-2 fixed (no sk- literal)" bash -c "! grep -qE '\"sk-[A-Za-z0-9]' src/paycli/report.py"

echo "== Agents / skills (frontmatter + Architect/Editor) =="
chk "agents+skills valid" $PY - <<'PY'
import re,glob,sys
ARCH={'bug-researcher','research-verifier','rca-analyst','rca-verifier','bug-planner','security-verifier'}
EDIT={'bug-fixer','unit-test-generator'}
ok=True
for p in glob.glob('agents/*.agent.md'):
    t=open(p).read(); m=re.match(r'^---\n(.*?)\n---',t,re.S); d={}
    for ln in (m.group(1).splitlines() if m else []):
        if ':' in ln: k,v=ln.split(':',1); d[k.strip()]=v.strip()
    n=d.get('name',''); tools=[x.strip() for x in d.get('tools','').split(',')]
    w={'Edit','Write','Bash'} & set(tools)
    if any(k not in d for k in ('name','description','tools','model')): ok=False
    if n in ARCH and (d.get('model')!='opus' or w): ok=False
    if n in EDIT and (d.get('model')!='sonnet' or not w): ok=False
q=open('skills/research-quality-measurement.md').read(); f=open('skills/unit-tests-FIRST.md').read()
if sum(x in q for x in ('Verified','Partially Verified','Unverified'))!=3: ok=False
if sum(x in f for x in ('Fast','Independent','Repeatable','Self-validating','Timely'))!=5: ok=False
sys.exit(0 if ok else 1)
PY

echo "== Docs =="
chk "README has author"          bash -c "grep -q 'Anton Tsiatsko' README.md"
chk "HOWTORUN present"           has HOWTORUN.md
chk "screenshots dir present"    test -d docs/screenshots

echo "== TASKS.md Expected Project Structure & Deliverables (pre-merge conformance) =="
# Required agents explicitly listed in TASKS.md (the 4 graded ones)
for a in research-verifier bug-fixer security-verifier unit-test-generator; do
  chk "agents/$a.agent.md" has "agents/$a.agent.md"; done
# Required skills
chk "skills/research-quality-measurement.md" has skills/research-quality-measurement.md
chk "skills/unit-tests-FIRST.md"             has skills/unit-tests-FIRST.md
# context/bugs/XXX artifacts (exact TASKS.md layout)
chk "context: bug-context.md"            has "$BUG/bug-context.md"
chk "context: research/codebase-research.md" has "$BUG/research/codebase-research.md"
chk "context: research/verified-research.md" has "$BUG/research/verified-research.md"
chk "context: implementation-plan.md"    has "$BUG/implementation-plan.md"
chk "context: fix-summary.md"            has "$BUG/fix-summary.md"
chk "context: security-report.md"        has "$BUG/security-report.md"
chk "context: test-report.md"            has "$BUG/test-report.md"
# app + tests + docs
chk "app source: src/paycli"             test -d src/paycli
chk "tests/ present"                      test -d tests
chk "docs/screenshots/ present"           test -d docs/screenshots
chk "README.md present"                   has README.md
chk "HOWTORUN.md present"                 has HOWTORUN.md
# 4 required screenshots (author-supplied; the only checks expected to fail until added)
for s in pipeline-run fixes-applied security-scan unit-tests; do
  chk "screenshot $s.png" has "docs/screenshots/$s.png"; done

echo ""
echo "RESULT: $pass passed, $fail failed."
[ "$fail" -eq 0 ]
