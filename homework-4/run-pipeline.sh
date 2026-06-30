#!/usr/bin/env bash
# Bug Coordinator — CONFIG-DRIVEN multi-agent bug-fix pipeline engine.
# Stages/order/paths/gates/permissions come from pipeline.config.json (per-agent model lives in
# agents/*.agent.md). WORK-Agents canonical flow + human checkpoints + immutable timestamped runs.
# Env overrides: PIPELINE_CONFIG, AUTO_APPROVE (1=auto-record, 0=interactive), PERM_MODE.
set -uo pipefail
HW="$(cd "$(dirname "$0")" && pwd)"; cd "$HW"
CONFIG="${PIPELINE_CONFIG:-pipeline.config.json}"
AUTO_APPROVE="${AUTO_APPROVE:-1}"

# --- preflight ---
command -v claude  >/dev/null 2>&1 || { echo "ERROR: 'claude' CLI not found on PATH"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found"; exit 1; }
[ -f "$CONFIG" ] || { echo "ERROR: config '$CONFIG' not found"; exit 1; }

# --- load global settings from config (env PERM_MODE overrides) ---
eval "$(python3 - "$CONFIG" <<'PY'
import json,sys,shlex
c=json.load(open(sys.argv[1]))
print("CFG_BUG="+shlex.quote(c["artifacts_dir"]))
print("CFG_PERM="+shlex.quote(c.get("permission_mode","acceptEdits")))
print("CFG_TOOLS="+shlex.quote(c.get("allowed_tools","Read,Grep,Glob,Edit,Write,Bash")))
PY
)"
BUG="$CFG_BUG"; PERM_MODE="${PERM_MODE:-$CFG_PERM}"; ALLOWED="$CFG_TOOLS"
[ -f "$BUG/bug-context.md" ] || { echo "ERROR: $BUG/bug-context.md missing"; exit 1; }
[ -d src/paycli ]            || { echo "ERROR: app src/paycli missing"; exit 1; }

# --- new immutable run folder ---
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"; RUN="$BUG/runs/run-$TS"
mkdir -p "$RUN" "$BUG/research"
GIT="$(git rev-parse --short HEAD 2>/dev/null || echo n/a)"
RLOG="$RUN/pipeline-run.log"; : > "$RLOG"
log(){ echo "$*" | tee -a "$RLOG"; }
log "=== Bug pipeline run-$TS (git $GIT · config $CONFIG · auto_approve=$AUTO_APPROVE · perm=$PERM_MODE) ==="

# --- register agents + skills for auto-discovery (per-agent frontmatter model honored) ---
mkdir -p .claude/agents .claude/skills
for f in agents/*.agent.md; do cp "$f" ".claude/agents/$(basename "${f%.agent.md}").md"; done
cp skills/*.md .claude/skills/ 2>/dev/null || true
"$HW/render-status.sh" "$RUN" >/dev/null 2>&1 || true

STAGES_JSON=""
finalize(){ local status="${1:-completed}"
  printf '{\n  "run_id": "run-%s",\n  "git": "%s",\n  "config": "%s",\n  "started": "%s",\n  "ended": "%s",\n  "status": "%s",\n  "perm_mode": "%s",\n  "stages": [%s]\n}\n' \
    "$TS" "$GIT" "$CONFIG" "$TS" "$(date -u +%FT%TZ)" "$status" "$PERM_MODE" "${STAGES_JSON%,}" > "$RUN/manifest.json"
}
run_stage(){ # nn agent output-relative-to-BUG prompt
  local nn="$1" ag="$2" canon="$3" prompt="$4"; prompt="${prompt//\{ARTIFACTS\}/$HW/$BUG}"
  local res="$RUN/${nn}-${ag}_result.md" lg="$RUN/${nn}-${ag}_log.md"
  local model; model="$(awk -F': ' '/^model:/{print $2; exit}' "agents/${ag}.agent.md")"
  log ">>> [$nn] $ag (model=$model)"
  "$HW/render-status.sh" "$RUN" "$nn" >/dev/null 2>&1 || true
  claude -p "${prompt}
Write your full structured result (ending with a '## Handoff -> next' section) to: $HW/$res
Write a compact decision log (Markdown table: | step | decision | reason | evidence |) to: $HW/$lg" \
    --append-system-prompt "$(cat "agents/${ag}.agent.md")" \
    --model "$model" --permission-mode "$PERM_MODE" --allowedTools "$ALLOWED" \
    < /dev/null >>"$RLOG" 2>&1   # </dev/null: stop claude from consuming the stage-loop's stdin
  if [ ! -s "$res" ]; then log "FAIL: $ag produced no result ($res)"; finalize "failed:$ag"; exit 2; fi
  if [ -n "$canon" ]; then mkdir -p "$(dirname "$HW/$BUG/$canon")"; cp "$res" "$HW/$BUG/$canon"; fi
  STAGES_JSON="$STAGES_JSON {\"step\":\"$nn\",\"agent\":\"$ag\"},"
  log "    ok -> $res${canon:+ , canonical $BUG/$canon}"
  "$HW/render-status.sh" "$RUN" >/dev/null 2>&1 || true
}
checkpoint(){ # nn n review-relative question
  local nn="$1" n="$2" review="$3" q="$4" verdict=""
  local cp="$RUN/${nn}-CHECKPOINT-${n}.md"
  if [ "$AUTO_APPROVE" = "1" ]; then verdict="APPROVED (auto)"
  else echo; echo "CHECKPOINT $n — review: $HW/$BUG/$review"; echo "Q: $q"
       read -r -p "Approve? [y/N] " a; [ "$a" = "y" ] && verdict="APPROVED" || verdict="REJECTED"; fi
  printf '# Checkpoint %s\n\n- Reviewed: `%s`\n- Question: %s\n- Decision: **%s**\n- At: %s (UTC)\n' \
    "$n" "$BUG/$review" "$q" "$verdict" "$(date -u +%FT%TZ)" > "$cp"
  log "--- CHECKPOINT $n: $verdict"
  "$HW/render-status.sh" "$RUN" >/dev/null 2>&1 || true
  case "$verdict" in *APPROVED*) ;; *) log "Checkpoint $n rejected — stopping."; finalize "rejected:cp$n"; exit 3;; esac
}

# --- drive stages from config (tab-separated) ---
# Field separator is US (\x1f), a NON-whitespace char, so empty config fields are preserved
# (IFS=$'\t' would collapse empties because tab is IFS-whitespace).
while IFS=$'\037' read -r nn kind agent output n review question prompt; do
  case "$kind" in
    agent)      run_stage  "$nn" "$agent" "$output" "$prompt" ;;
    checkpoint) checkpoint "$nn" "$n" "$review" "$question" ;;
    *) [ -n "$kind" ] && log "skip unknown stage kind: $kind" ;;
  esac
done < <(python3 - "$CONFIG" <<'PY'
import json,sys
SEP="\x1f"
for s in json.load(open(sys.argv[1]))["stages"]:
    row=[str(s.get(k,"")).replace("\x1f"," ").replace("\n"," ") for k in ("nn","kind","agent","output","n","review","question","prompt")]
    print(SEP.join(row))
PY
)

finalize completed
"$HW/render-status.sh" "$RUN" >/dev/null 2>&1 || true
log "=== DONE -> $RUN ==="
echo "Artifacts in run folder:"; ls -1 "$RUN"
