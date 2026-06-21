<#  Bug Coordinator (PowerShell) — single-command 4-agent (+ helper) bug-fix pipeline.
    Cross-platform mirror of run-pipeline.sh: WORK-Agents canonical flow + 2 human checkpoints
    + immutable timestamped run folders. Usage: pwsh ./run-pipeline.ps1   (env AUTO_APPROVE=0 for interactive) #>
$ErrorActionPreference = "Stop"
$HW  = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $HW
$BUG = "context/bugs/001"
$AUTO = if ($env:AUTO_APPROVE) { $env:AUTO_APPROVE } else { "1" }
$PERM = if ($env:PERM_MODE) { $env:PERM_MODE } else { "acceptEdits" }

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Error "'claude' CLI not found on PATH"; exit 1 }
if (-not (Test-Path "$BUG/bug-context.md")) { Write-Error "$BUG/bug-context.md missing"; exit 1 }
if (-not (Test-Path "src/paycli")) { Write-Error "app src/paycli missing"; exit 1 }

$TS  = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH-mm-ssZ")
$RUN = "$BUG/runs/run-$TS"
New-Item -ItemType Directory -Force -Path $RUN, "$BUG/research" | Out-Null
$GIT = (git rev-parse --short HEAD 2>$null); if (-not $GIT) { $GIT = "n/a" }
$RLOG = "$RUN/pipeline-run.log"; "" | Set-Content $RLOG
function Log($m) { $m | Tee-Object -FilePath $RLOG -Append }
Log "=== Bug pipeline run-$TS (git $GIT, auto_approve=$AUTO) ==="

New-Item -ItemType Directory -Force -Path ".claude/agents", ".claude/skills" | Out-Null
Get-ChildItem agents/*.agent.md | ForEach-Object { Copy-Item $_.FullName ".claude/agents/$($_.BaseName -replace '\.agent$','').md" -Force }
Copy-Item skills/*.md ".claude/skills/" -Force -ErrorAction SilentlyContinue

$script:STAGES = @()
function Finalize($status="completed") {
  $stagesJson = ($script:STAGES -join ", ")
  @"
{ "run_id": "run-$TS", "git": "$GIT", "started": "$TS",
  "ended": "$((Get-Date).ToUniversalTime().ToString('s'))Z", "status": "$status",
  "auto_approve": $AUTO, "stages": [$stagesJson] }
"@ | Set-Content "$RUN/manifest.json"
}
function Run-Stage($nn, $ag, $canon, $prompt) {
  $res = "$RUN/$nn-${ag}_result.md"; $lg = "$RUN/$nn-${ag}_log.md"
  $model = ((Select-String -Path "agents/$ag.agent.md" -Pattern '^model:\s*(.+)$').Matches[0].Groups[1].Value).Trim()
  Log ">>> [$nn] $ag (model=$model)"
  $full = "$prompt`nWrite your full structured result (ending with a '## Handoff -> next' section) to: $HW/$res`nWrite a compact decision log (Markdown table: | step | decision | reason | evidence |) to: $HW/$lg"
  claude -p $full --append-system-prompt (Get-Content "agents/$ag.agent.md" -Raw) --model $model --permission-mode $PERM --allowedTools "Read,Grep,Glob,Edit,Write,Bash(.venv/bin/python:*),Bash(python:*),Bash(python3:*),Bash(pytest:*),Bash(ls:*),Bash(cat:*)" *>> $RLOG
  if (-not (Test-Path $res) -or (Get-Item $res).Length -eq 0) { Log "FAIL: $ag produced no result"; Finalize "failed:$ag"; exit 2 }
  if ($canon) { Copy-Item $res "$HW/$canon" -Force }
  $script:STAGES += "{""step"":""$nn"",""agent"":""$ag""}"
  Log "    ok -> $res"
}
function Checkpoint($nn, $n, $art, $q) {
  $cp = "$RUN/$nn-CHECKPOINT-$n.md"
  if ($AUTO -eq "1") { $verdict = "APPROVED (auto)" }
  else { Write-Host "`nCHECKPOINT $n — review: $HW/$art`nQ: $q"; $a = Read-Host "Approve? [y/N]"; $verdict = if ($a -eq "y") { "APPROVED" } else { "REJECTED" } }
  "# Checkpoint $n`n`n- Reviewed: ``$art```n- Question: $q`n- Decision: **$verdict**`n- At: $((Get-Date).ToUniversalTime().ToString('s'))Z (UTC)" | Set-Content $cp
  Log "--- CHECKPOINT $n: $verdict"
  if ($verdict -notlike "*APPROVED*") { Log "Checkpoint $n rejected — stopping."; Finalize "rejected:cp$n"; exit 3 }
}

Run-Stage "00" "bug-researcher"      "$BUG/research/codebase-research.md" "Read $HW/$BUG/bug-context.md and document each seeded issue with exact file:line evidence from $HW/src."
Run-Stage "01" "research-verifier"   "$BUG/research/verified-research.md" "Verify $HW/$BUG/research/codebase-research.md against $HW/src using the research-quality-measurement skill."
Run-Stage "02" "rca-analyst"         "$BUG/rca.md"                        "Read $HW/$BUG/research/verified-research.md and produce a 5-Whys root-cause chain per issue."
Run-Stage "03" "rca-verifier"        "$BUG/verified-rca.md"               "Validate the 5-Whys chains in $HW/$BUG/rca.md."
Checkpoint "04" "1" "$BUG/verified-rca.md"        "Is the root cause correct and are we fixing the right thing?"
Run-Stage "05" "bug-planner"         "$BUG/implementation-plan.md"        "Read $HW/$BUG/verified-rca.md and write a before/after implementation plan with a test command per change."
Checkpoint "06" "2" "$BUG/implementation-plan.md" "Are the changes appropriate, correctly scoped, and free of missing edge cases?"
Run-Stage "07" "bug-fixer"           "$BUG/fix-summary.md"                "Execute $HW/$BUG/implementation-plan.md; run '.venv/bin/python -m pytest tests/' after each change; stop on failure."
Run-Stage "08" "security-verifier"   "$BUG/security-report.md"            "Security-review the files changed per $HW/$BUG/fix-summary.md; report only (no edits)."
Run-Stage "09" "unit-test-generator" "$BUG/test-report.md"               "Generate FIRST tests for the changed code (BUG-A boundary, BUG-B empty, VULN-1 injection-blocked) under $HW/tests and run pytest with coverage."

Finalize "completed"
Log "=== DONE -> $RUN ==="
Get-ChildItem $RUN | Select-Object Name
