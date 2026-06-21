#!/usr/bin/env bash
# render-status.sh RUN_DIR [CURRENT_STEP]
# Writes <RUN_DIR>/pipeline-status.html — a self-contained (no-CDN) live status board
# with per-stage links to each agent's log + result. The coordinator calls this after
# each stage so the board updates as agents run.
set -uo pipefail
RUN="${1:?usage: render-status.sh RUN_DIR [CURRENT_STEP]}"
CUR="${2:-}"
OUT="$RUN/pipeline-status.html"
REL="../../../../.."             # run folder -> homework-4 root (links to src/, tests/, PR)
PR_URL="${PR_URL:-}"

# NN|label|model|kind|result-file|graded
STAGES=(
"00|bug-researcher|opus|agent|00-bug-researcher_result.md|"
"01|research-verifier|opus|agent|01-research-verifier_result.md|⭐"
"02|rca-analyst|opus|agent|02-rca-analyst_result.md|"
"03|rca-verifier|opus|agent|03-rca-verifier_result.md|"
"04|CHECKPOINT 1|human|cp|04-CHECKPOINT-1.md|"
"05|bug-planner|opus|agent|05-bug-planner_result.md|"
"06|CHECKPOINT 2|human|cp|06-CHECKPOINT-2.md|"
"07|bug-fixer|sonnet|agent|07-bug-fixer_result.md|⭐"
"08|security-verifier|opus|agent|08-security-verifier_result.md|⭐"
"09|unit-test-generator|sonnet|agent|09-unit-test-generator_result.md|⭐"
)
lnk(){ [ -s "$RUN/$1" ] && echo "<a href=\"$1\">$2</a>" || echo "<span class=dim>$2</span>"; }

boxes=""; rows=""
for s in "${STAGES[@]}"; do
  IFS='|' read -r nn label model kind file graded <<<"$s"
  if [ -s "$RUN/$file" ]; then st=done; elif [ "$nn" = "$CUR" ]; then st=running; else st=pending; fi
  if [ "$kind" = "cp" ]; then
    flog="—"; fres="$(lnk "$file" record)"; blinks="$(lnk "$file" record)"
  else
    lf="${file/_result.md/_log.md}"; flog="$(lnk "$lf" log)"; fres="$(lnk "$file" result)"
    blinks="$(lnk "$lf" log) · $(lnk "$file" result)"
  fi
  boxes+="<div class=\"box $st $kind\"><span class=\"n\">$nn</span> ${label} ${graded}<br><small>${model} · ${st}</small><div class=\"links\">${blinks}</div></div>"
  [ "$nn" != "09" ] && boxes+="<div class=\"arrow\">▸</div>"
  rows+="<tr><td>${nn}</td><td>${label} ${graded}</td><td>${model}</td><td class=\"${st}\">${st}</td><td>${flog}</td><td>${fres}</td></tr>"
done
status=$(grep -o '"status": *"[^"]*"' "$RUN/manifest.json" 2>/dev/null | head -1 | sed 's/.*: *"//;s/"//')
toplinks="$(lnk manifest.json manifest.json) · $(lnk pipeline-run.log pipeline-run.log)"
outputs="<li><b>Fixes (changed source):</b> <a href=\"$REL/src/paycli/transactions.py\">transactions.py</a> · <a href=\"$REL/src/paycli/report.py\">report.py</a> · <a href=\"$REL/context/bugs/001/fix-summary.md\">fix-summary.md</a></li>"
outputs+="<li><b>Reports &amp; tests:</b> <a href=\"$REL/context/bugs/001/security-report.md\">security-report.md</a> · <a href=\"$REL/context/bugs/001/test-report.md\">test-report.md</a> · <a href=\"$REL/tests/test_generated.py\">generated tests</a></li>"
[ -n "$PR_URL" ] && outputs+="<li><b>Pull request:</b> <a href=\"$PR_URL\">$PR_URL</a></li>"
cat > "$OUT" <<HTML
<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Bug-Fix Pipeline status</title>
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#e6edf3;margin:28px}
 h1{font-size:19px;margin:0 0 4px} .meta{color:#8b949e;font-size:13px;margin-bottom:6px}
 a{color:#58a6ff;text-decoration:none} a:hover{text-decoration:underline} .dim{color:#6e7681}
 .flow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:18px 0 8px}
 .box{border-radius:9px;padding:9px 13px;min-width:140px;font-size:13px;font-weight:600;text-align:center;line-height:1.35}
 .box small{font-weight:400;opacity:.9} .box .n{opacity:.7;margin-right:4px}
 .box .links{margin-top:5px;font-size:11px;font-weight:400}
 .done{background:#1f7a33;color:#fff} .pending{background:#30363d;color:#8b949e}
 .running{background:#1f6feb;color:#fff} .cp.done{background:#9e6a00;color:#fff} .cp.pending{background:#30363d;color:#8b949e}
 .box.done .links a,.box.running .links a{color:#cfe8ff} .arrow{color:#6e7681;font-size:18px}
 table{border-collapse:collapse;font-size:13px;margin-top:14px} td,th{border:1px solid #30363d;padding:5px 11px;text-align:left}
 th{color:#8b949e;font-weight:600} td.done{color:#3fb950} td.pending{color:#8b949e} td.running{color:#58a6ff}
 .legend{margin-top:14px;font-size:12px;color:#8b949e}
 h2{font-size:15px;margin:20px 0 6px} ul.outputs{font-size:13px;line-height:1.8;margin:0;padding-left:18px}
</style></head><body>
 <h1>🤖 Bug-Fix Pipeline — $(basename "$RUN")</h1>
 <div class="meta">run status: <b>${status:-running}</b> &nbsp;·&nbsp; Architect = Opus (read-only) &nbsp;·&nbsp; Editor = Sonnet (write) &nbsp;·&nbsp; ⭐ = required graded agent</div>
 <div class="meta">run files: ${toplinks}</div>
 <div class="flow">${boxes}</div>
 <table><tr><th>#</th><th>stage</th><th>model</th><th>status</th><th>log</th><th>result</th></tr>${rows}</table>
 <h2>Outputs (fixes · reports · PR)</h2><ul class="outputs">${outputs}</ul>
 <div class="legend">● green = done &nbsp; ● amber = human checkpoint &nbsp; ● blue = running &nbsp; ● grey = pending &nbsp;|&nbsp; click <b>log</b>/<b>result</b> to open each stage's files</div>
</body></html>
HTML
echo "$OUT"
