#!/usr/bin/env bash
# Bug Coordinator — single-command 4-agent (+ helper) bug-fix pipeline.
# Implements the WORK-Agents canonical flow with 2 human checkpoints and immutable run folders.
set -uo pipefail

HW="$(cd "$(dirname "$0")" && pwd)"; cd "$HW"
BUG="context/bugs/001"
AUTO_APPROVE="${AUTO_APPROVE:-1}"   # 1 = record verdict + continue (demo); 0 = interactive prompt
PERM_MODE="${PERM_MODE:-acceptEdits}"  # acceptEdits (default/safe) | bypassPermissions (unattended run)

# --- preflight -------------------------------------------------------------
command -v claude >/dev/null 2>&1 || { echo "ERROR: 'claude' CLI not found on PATH"; exit 1; }
[ -f "$BUG/bug-context.md" ] || { echo "ERROR: $BUG/bug-context.md missing"; exit 1; }
[ -d src/paycli ]            || { echo "ERROR: app src/paycli missing"; exit 1; }

# --- new immutable run folder ---------------------------------------------
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
RUN="$BUG/runs/run-$TS"
mkdir -p "$RUN" "$BUG/research"
GIT="$(git rev-parse --short HEAD 2>/dev/null || echo n/a)"
RLOG="$RUN/pipeline-run.log"; : > "$RLOG"
log(){ echo "$*" | tee -a "$RLOG"; }
log "=== Bug pipeline run-$TS (git $GIT, auto_approve=$AUTO_APPROVE) ==="

# --- register agents + skills for auto-discovery (frontmatter model honored) -
mkdir -p .claude/agents .claude/skills
for f in agents/*.agent.md; do cp "$f" ".claude/agents/$(basename "${f%.agent.md}").md"; done
cp skills/*.md .claude/skills/ 2>/dev/null || true

STAGES=""
finalize(){ # status
  local status="${1:-completed}"
  printf '{\n  "run_id": "run-%s",\n  "git": "%s",\n  "started": "%s",\n  "ended": "%s",\n  "status": "%s",\n  "auto_approve": %s,\n  "stages": [%s]\n}\n' \
    "$TS" "$GIT" "$TS" "$(date -u +%FT%TZ)" "$status" "$AUTO_APPROVE" "${STAGES%,}" > "$RUN/manifest.json"
}
run_stage(){ # nn agent canonical "prompt"
  local nn="$1" ag="$2" canon="$3" prompt="$4"
  local res="$RUN/${nn}-${ag}_result.md" lg="$RUN/${nn}-${ag}_log.md"
  local model; model="$(awk -F': ' '/^model:/{print $2; exit}' "agents/${ag}.agent.md")"
  log ">>> [$nn] $ag (model=$model)"
  # The agent definition is injected as the system prompt (honors its model); registered
  # subagents + skills in .claude/ are also auto-discovered.
  claude -p "${prompt}
Write your full structured result (ending with a '## Handoff -> next' section) to: $HW/$res
Write a compact decision log (Markdown table: | step | decision | reason | evidence |) to: $HW/$lg" \
    --append-system-prompt "$(cat "agents/${ag}.agent.md")" \
    --model "$model" --permission-mode "$PERM_MODE" \
    --allowedTools "Read,Grep,Glob,Edit,Write,Bash(.venv/bin/python:*),Bash(python:*),Bash(python3:*),Bash(pytest:*),Bash(ls:*),Bash(cat:*)" >>"$RLOG" 2>&1
  if [ ! -s "$res" ]; then log "FAIL: $ag produced no result ($res)"; finalize "failed:$ag"; exit 2; fi
  [ -n "$canon" ] && cp "$res" "$HW/$canon"
  STAGES="$STAGES {\"step\":\"$nn\",\"agent\":\"$ag\",\"result\":\"${nn}-${ag}_result.md\"},"
  log "    ok -> $res${canon:+ , canonical $canon}"
}
checkpoint(){ # nn N artifact "question"
  local nn="$1" n="$2" art="$3" q="$4" verdict=""
  local cp="$RUN/${nn}-CHECKPOINT-${n}.md"
  if [ "$AUTO_APPROVE" = "1" ]; then verdict="APPROVED (auto)"
  else echo; echo "CHECKPOINT $n — review: $HW/$art"; echo "Q: $q"
       read -r -p "Approve? [y/N] " a; [ "$a" = "y" ] && verdict="APPROVED" || verdict="REJECTED"; fi
  printf '# Checkpoint %s\n\n- Reviewed: `%s`\n- Question: %s\n- Decision: **%s**\n- At: %s (UTC)\n' \
    "$n" "$art" "$q" "$verdict" "$(date -u +%FT%TZ)" > "$cp"
  log "--- CHECKPOINT $n: $verdict"
  case "$verdict" in *APPROVED*) ;; *) log "Checkpoint $n rejected — stopping."; finalize "rejected:cp$n"; exit 3;; esac
}

# --- pipeline (sequential; canonical flow + 2 human checkpoints) -----------
run_stage 00 bug-researcher      "$BUG/research/codebase-research.md" "Read $HW/$BUG/bug-context.md and document each seeded issue with exact file:line evidence from $HW/src."
run_stage 01 research-verifier   "$BUG/research/verified-research.md" "Verify $HW/$BUG/research/codebase-research.md against $HW/src using the research-quality-measurement skill."
run_stage 02 rca-analyst         "$BUG/rca.md"                        "Read $HW/$BUG/research/verified-research.md and produce a 5-Whys root-cause chain per issue."
run_stage 03 rca-verifier        "$BUG/verified-rca.md"               "Validate the 5-Whys chains in $HW/$BUG/rca.md."
checkpoint 04 1 "$BUG/verified-rca.md"        "Is the root cause correct and are we fixing the right thing?"
run_stage 05 bug-planner         "$BUG/implementation-plan.md"        "Read $HW/$BUG/verified-rca.md and write a before/after implementation plan with a test command per change."
checkpoint 06 2 "$BUG/implementation-plan.md" "Are the changes appropriate, correctly scoped, and free of missing edge cases?"
run_stage 07 bug-fixer           "$BUG/fix-summary.md"                "Execute $HW/$BUG/implementation-plan.md; run '.venv/bin/python -m pytest tests/' after each change; stop on failure."
run_stage 08 security-verifier   "$BUG/security-report.md"            "Security-review the files changed per $HW/$BUG/fix-summary.md; report only (no edits)."
run_stage 09 unit-test-generator "$BUG/test-report.md"               "Generate FIRST tests for the changed code (BUG-A boundary, BUG-B empty, VULN-1 injection-blocked) under $HW/tests and run pytest with coverage."

finalize completed
log "=== DONE -> $RUN ==="
echo "Artifacts in run folder:"; ls -1 "$RUN"
