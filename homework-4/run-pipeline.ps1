<#  Bug Coordinator (PowerShell) — CONFIG-DRIVEN multi-agent bug-fix pipeline engine.
    Reads pipeline.config.json (stages/order/paths/gates/permissions); per-agent model lives in
    agents/*.agent.md. Env overrides: PIPELINE_CONFIG, AUTO_APPROVE, PERM_MODE.
    Usage: pwsh ./run-pipeline.ps1 #>
$ErrorActionPreference = "Stop"
$HW = Split-Path -Parent $MyInvocation.MyCommand.Path; Set-Location $HW
$CONFIG = if ($env:PIPELINE_CONFIG) { $env:PIPELINE_CONFIG } else { "pipeline.config.json" }
$AUTO   = if ($env:AUTO_APPROVE) { $env:AUTO_APPROVE } else { "1" }

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Error "'claude' CLI not found"; exit 1 }
if (-not (Test-Path $CONFIG)) { Write-Error "config '$CONFIG' not found"; exit 1 }
$cfg = Get-Content $CONFIG -Raw | ConvertFrom-Json
$BUG = $cfg.artifacts_dir
$PERM = if ($env:PERM_MODE) { $env:PERM_MODE } else { $cfg.permission_mode }
$ALLOWED = $cfg.allowed_tools
if (-not (Test-Path "$BUG/bug-context.md")) { Write-Error "$BUG/bug-context.md missing"; exit 1 }
if (-not (Test-Path "src/paycli")) { Write-Error "app src/paycli missing"; exit 1 }

$TS = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH-mm-ssZ")
$RUN = "$BUG/runs/run-$TS"
New-Item -ItemType Directory -Force -Path $RUN, "$BUG/research" | Out-Null
$GIT = (git rev-parse --short HEAD 2>$null); if (-not $GIT) { $GIT = "n/a" }
$RLOG = "$RUN/pipeline-run.log"; "" | Set-Content $RLOG
function Log($m) { $m | Tee-Object -FilePath $RLOG -Append }
Log "=== Bug pipeline run-$TS (git $GIT · config $CONFIG · auto=$AUTO · perm=$PERM) ==="

New-Item -ItemType Directory -Force -Path ".claude/agents", ".claude/skills" | Out-Null
Get-ChildItem agents/*.agent.md | ForEach-Object { Copy-Item $_.FullName ".claude/agents/$($_.BaseName -replace '\.agent$','').md" -Force }
Copy-Item skills/*.md ".claude/skills/" -Force -ErrorAction SilentlyContinue
& "$HW/render-status.sh" $RUN 2>$null

$script:STAGES = @()
function Finalize($status="completed") {
  @"
{ "run_id":"run-$TS","git":"$GIT","config":"$CONFIG","started":"$TS",
  "ended":"$((Get-Date).ToUniversalTime().ToString('s'))Z","status":"$status","perm_mode":"$PERM",
  "stages":[$($script:STAGES -join ', ')] }
"@ | Set-Content "$RUN/manifest.json"
}
function Run-Stage($nn,$ag,$canon,$prompt) {
  $prompt = $prompt -replace '\{ARTIFACTS\}', "$HW/$BUG"
  $res = "$RUN/$nn-${ag}_result.md"; $lg = "$RUN/$nn-${ag}_log.md"
  $model = ((Select-String -Path "agents/$ag.agent.md" -Pattern '^model:\s*(.+)$').Matches[0].Groups[1].Value).Trim()
  Log ">>> [$nn] $ag (model=$model)"
  $full = "$prompt`nWrite your full structured result (ending with a '## Handoff -> next' section) to: $HW/$res`nWrite a compact decision log (Markdown table: | step | decision | reason | evidence |) to: $HW/$lg"
  claude -p $full --append-system-prompt (Get-Content "agents/$ag.agent.md" -Raw) --model $model --permission-mode $PERM --allowedTools $ALLOWED *>> $RLOG
  if (-not (Test-Path $res) -or (Get-Item $res).Length -eq 0) { Log "FAIL: $ag produced no result"; Finalize "failed:$ag"; exit 2 }
  if ($canon) { New-Item -ItemType Directory -Force -Path (Split-Path "$HW/$BUG/$canon") | Out-Null; Copy-Item $res "$HW/$BUG/$canon" -Force }
  $script:STAGES += "{""step"":""$nn"",""agent"":""$ag""}"
  Log "    ok -> $res"; & "$HW/render-status.sh" $RUN 2>$null
}
function Checkpoint($nn,$n,$review,$q) {
  $cp = "$RUN/$nn-CHECKPOINT-$n.md"
  if ($AUTO -eq "1") { $verdict = "APPROVED (auto)" }
  else { Write-Host "`nCHECKPOINT $n — review: $HW/$BUG/$review`nQ: $q"; $a = Read-Host "Approve? [y/N]"; $verdict = if ($a -eq "y") { "APPROVED" } else { "REJECTED" } }
  "# Checkpoint $n`n`n- Reviewed: ``$BUG/$review```n- Question: $q`n- Decision: **$verdict**`n- At: $((Get-Date).ToUniversalTime().ToString('s'))Z (UTC)" | Set-Content $cp
  Log "--- CHECKPOINT $n: $verdict"; & "$HW/render-status.sh" $RUN 2>$null
  if ($verdict -notlike "*APPROVED*") { Log "Checkpoint $n rejected — stopping."; Finalize "rejected:cp$n"; exit 3 }
}

foreach ($s in $cfg.stages) {
  if ($s.kind -eq "agent") { Run-Stage $s.nn $s.agent $s.output $s.prompt }
  elseif ($s.kind -eq "checkpoint") { Checkpoint $s.nn $s.n $s.review $s.question }
}
Finalize "completed"; & "$HW/render-status.sh" $RUN 2>$null
Log "=== DONE -> $RUN ==="; Get-ChildItem $RUN | Select-Object Name
