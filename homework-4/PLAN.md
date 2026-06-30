# Homework 4 — Implementation Plan (4-Agent Bug-Fix Pipeline)

> Build plan for an end-to-end, single-command **agentic bug-fix pipeline** that operates on a
> small seeded application, fixes its bugs, security-reviews the changes, and generates unit tests.
> Treat every **Non-Functional & Policy**, **AI-Usage Standard**, and **PR/Formatting** rule below as
> a binding acceptance constraint, not background. Every build task names the requirement it serves.

**Status:** Aligned to Alexey-Popov's *WORK-Agents* guide · **Version:** 2.0 · **Author:** Anton Tsiatsko ·
**Date:** 2026-06-21 · **Target dir:** `homework-4/` · **Stack:** Python 3.11+

> ⚠️ The HW4 TASKS "Expected Project Structure" header reads `homework-5/` — that is an **upstream
> typo**; all work lives in **`homework-4/`**. Where Task 1 says `research/codebase-research.md` and
> the structure says `context/bugs/XXX/research/…`, the **`context/bugs/001/…`** layout is canonical
> (matches the accepted reference submission).

### Contents
[How to use](#how-to-use-this-plan) · [Objectives](#objectives) · [Non-Functional & Policy](#non-functional--policy) ·
[AI-Usage Standards](#ai-usage-standards) · [Assumptions](#assumptions) · [Architecture & Pipeline](#architecture--pipeline-flow) ·
[Sample App & Seeded Issues](#sample-app--seeded-issues) · [Artifact Contracts](#artifact-contracts) ·
[Agent Specs](#agent-specifications) · [Skill Specs](#skill-specifications) · [Single-Command Pipeline](#single-command-pipeline) ·
[Low-Level Build Tasks](#low-level-build-tasks) · [Edge Cases](#edge-cases--failure-modes) ·
[Verification](#verification) · [PR & Submission](#pr--submission-plan) · [Traceability](#traceability-matrix)

---

## How to use this plan
- **Closed-world:** build exactly what this plan defines; do not invent extra agents, files, or
  scope. If a HW4 requirement seems uncovered, update this plan first, then build.
- **Order matters:** follow *Low-Level Build Tasks* top-to-bottom; each ends in a Definition of Done.
- **Trace everything:** every artifact/agent maps to a HW4 task in the *Traceability Matrix*.
- **Evidence over assertion:** the pipeline must actually run and produce committed artifacts +
  screenshots; "done" = artifacts exist, tests pass post-fix, quality gate green.

## Objectives

### High-Level Objective
Deliver a reproducible, **single-command** 4-agent pipeline (plus 2 helper stages) that takes a
seeded sample app with **2 real bugs + 1 real security vulnerability**, verifies the research, fixes
the bugs, security-reviews the changed code, and generates FIRST-compliant unit tests — producing a
graded-quality PR that satisfies every HW4 deliverable and every Alexey-Popov review expectation.

### Mid-Level Objectives (observable)
| ID | Objective | Observable success signal |
|----|-----------|---------------------------|
| **M1** | Bug Research Verifier fact-checks researcher output using a quality skill | `verified-research.md` exists with all required sections + a Research Quality level from the skill; every `file:line` verified |
| **M2** | Bug Fixer applies the plan and documents changes, running tests after each | `fix-summary.md` lists before/after + test result per change; seeded bugs fixed |
| **M3** | Security Verifier reviews changed code (report only) | `security-report.md` rates each finding CRITICAL–INFO with `file:line` + remediation; no code edited by it |
| **M4** | Unit Test Generator creates FIRST tests for changed code and runs them | `test-report.md` + `tests/` exist; tests pass; FIRST skill referenced |
| **M5** | Sample app demonstrates before→after | app runs; 2 bugs + 1 vuln present before, resolved after; `pytest` green post-fix |
| **M6** | Whole pipeline runs from one command, auto-loading skills | `./run-pipeline.sh` (and `.ps1`) runs all 8 stages + 2 checkpoints in order with gates; artifacts regenerated |
| **M7** | Each agent has an explicit, justified model | every `*.agent.md` has a `model:`; README justifies each choice |
| **M8** | PR + docs satisfy course/reviewer formatting | README (author, how-to-run, model table, task-coverage), HOWTORUN, PR with **embedded** screenshots |

## Non-Functional & Policy
- **Engineering quality gate (must pass):** `ruff` (lint+imports), `mypy` (types), `bandit`
  (security — must flag the seeded vuln pre-fix and pass post-fix), `radon` (no C-or-worse), `pytest`
  with **coverage ≥ 90% measured on `src/paycli/`** (post-fix). Consistent with HW1–HW3 (Alexey approved this gate).
- **Security:** report-only agents must be **read-only by tool scope** (cannot edit). No secrets in
  committed code post-fix (the seeded secret is remediated to env/config) — and no real secrets/PII
  in committed **artifacts or screenshots** either.
- **Reproducibility:** single command re-runs the pipeline from a clean state; cross-platform
  (`.sh` + `.ps1`). All paths forward-slash; no machine-specific absolute paths.
- **Determinism of artifacts:** artifact files have a fixed section schema (see *Artifact Contracts*)
  so a reviewer can verify completeness at a glance.
- **Money correctness:** sample app uses integer minor units / `Decimal` (never `float`) **after**
  fix; the pre-fix `float` handling is one of the seeded bugs.

## AI-Usage Standards
Applies the subagent + skill best practices researched for HW4.
- **Subagents:** one focused responsibility each; frontmatter `name` (kebab), third-person
  `description` written as *"Use when…"* triggers, **least-privilege `tools`**, explicit `model`.
- **Skills:** concise SKILL.md (< 500 lines), gerund/noun name, third-person "what + when"
  description, template/checklist patterns, references one level deep, no time-sensitive content.
- **Pipeline = prompt-chaining workflow** (Anthropic "Building Effective Agents"): fixed stages +
  validation gates; transparency via the committed artifact at each stage. Keep it simple.
- **Architect / Editor split (per the WORK-Agents guide, p.4):** **Architect** agents *plan / research
  / verify* — **read-only**, **Opus** ("what should we do?"): `bug-researcher`, `research-verifier`,
  `rca-analyst`, `rca-verifier`, `bug-planner`, `security-verifier`. **Editor** agents *implement* —
  **write**, **Sonnet** ("how do we do it?"): `bug-fixer` (implementer), `unit-test-generator`.
  Rationale: Architect thinks deeply, Editor acts quickly; ~5× cost difference → right model per task.
  Use the `opus`/`sonnet` model aliases (real, version-current) — never placeholders. Justify in README.

## Assumptions
- Pipeline is driven by Claude Code in headless mode (`claude -p`) per stage; the run script
  registers the agents/skills so Claude auto-discovers them (symlink/copy into `.claude/`).
- One bug batch (`context/bugs/001/`) is sufficient to demonstrate the full flow.
- The graded agents are the **4 required**; `bug-researcher` and `bug-planner` are helper stages
  included so the single command is genuinely end-to-end (they produce the inputs the 4 consume).
- Screenshots are captured by the author after a real run and embedded in the PR description.

## Architecture & Pipeline Flow
Sequential (no parallelism), file-based hand-off, orchestrated by the **Bug Coordinator** (the run
script), with **two human checkpoints** — the *WORK-Agents* canonical pipeline (p.7) extended with
HW4's security & test stages. Architect agents are read-only (Opus); Editor agents write (Sonnet).
```
context.md
 → bug-researcher (A)     → research/codebase-research.md
 → research-verifier (A)  → verified-research.md            [Task 1 ⭐]
 → rca-analyst (A)        → rca.md  (5 Whys root cause)
 → rca-verifier (A)       → verified-rca.md
 ── ⛔ CHECKPOINT 1 — human: "is the root cause correct? fixing the right thing?" → approve ──
 → bug-planner (A)        → implementation-plan.md
 ── ⛔ CHECKPOINT 2 — human: "are the changes appropriate / scoped? edge cases?" → approve ──
 → bug-fixer (E)          → fix-summary.md (+ edited src)    [Task 2 ⭐⭐]
 → security-verifier (A)  → security-report.md               [Task 3 ⭐⭐]
 → unit-test-generator(E) → test-report.md + tests/          [Task 4 ⭐⭐⭐]
  (A) = Architect / Opus / read-only      (E) = Editor / Sonnet / write
```
- **Automatic gates:** stop if research or RCA is `Unverified`; stop if a fix's tests fail.
- **Human checkpoints:** CP1 before planning, CP2 before implementation — see *Human Checkpoints*.
  "Agents do research, humans make decisions."
- **Reflection loop (p.5):** Editor agents reflect on execution output/errors and iterate
  (run → read errors → revise → re-run) before finalizing their result.
- **Immutability (p.5):** each phase writes its artifact once per run and never mutates an earlier
  phase's; a re-run creates a **new timestamped run folder** (see *Run Capture & Traceability*).
- **Skill auto-load:** `research-verifier`→`research-quality-measurement`,
  `unit-test-generator`→`unit-tests-FIRST` (the coordinator registers them).

## Sample App & Seeded Issues
**App:** `paycli` — a tiny Python payments/transactions CLI (FinTech-themed, consistent with the course).
```
src/paycli/
  __init__.py
  transactions.py   # totals, daily-limit check, average  (Bug A, Bug B)
  report.py         # export feature                       (Vuln 1; seeded secret = Vuln 2)
  cli.py            # entry point: `python -m paycli ...`
pyproject.toml      # deps + ruff/mypy/bandit/radon/pytest config
tests/test_baseline.py  # AUTHOR baseline suite: encodes correct behaviour
```
**Baseline tests (critical for the fixer's loop):** the app ships a small **author-written baseline
suite** that encodes the *correct* behaviour and therefore **fails pre-fix and passes post-fix**.
This is what `bug-fixer` runs "after each change" (Task 2) and what proves before→after (M5). The
`unit-test-generator` later **adds** FIRST tests for the changed code (it does not duplicate the baseline).

**Seeded issues** (documented in `context/bugs/001/bug-context.md`):
| ID | Type | Location | Defect | Fix |
|----|------|----------|--------|-----|
| BUG-A | Logic / boundary | `transactions.is_within_daily_limit` | uses `spent+amount < limit` → off-by-one rejects spend exactly at limit | use `<=`; add boundary test |
| BUG-B | Edge case | `transactions.average_transaction` | divides by `len` with no empty-list guard → `ZeroDivisionError` | return `0`/`Decimal(0)` on empty |
| VULN-1 | Command injection (HIGH) | `report.export_report` | `subprocess.run(f"… {path}", shell=True)` on user path | argv list, `shell=False`, validate path |
| VULN-2 | Hardcoded secret (MEDIUM) | `report.API_KEY = "sk-live-…"` | secret in source | move to env var; remove literal |
> Money handling in `transactions` uses `float` pre-fix (latent correctness risk) → fix migrates to
> `Decimal`/minor units, reinforcing the M-rule and giving the test generator a clear target.

## Artifact Contracts
Each stage writes one file under `context/bugs/001/` with a fixed schema (reviewer-verifiable):
- **`bug-context.md`** — author-written: app summary, the 4 seeded issues (table above), how to reproduce each.
- **`research/codebase-research.md`** (bug-researcher) — claims with exact `file:line` + code snippets per issue.
- **`research/verified-research.md`** (research-verifier; **per skill**) — sections: *Verification Summary* (pass/fail + Research Quality), *Verified Claims*, *Discrepancies Found*, *Research Quality Assessment* (level + reasoning), *References*.
- **`rca.md`** (rca-analyst) — root cause via **5 Whys** per issue: Symptom → Why1…Why5 → Root Cause; one chain per seeded issue.
- **`verified-rca.md`** (rca-verifier) — validates each 5-Whys chain (sound? evidence-backed?) → pass/fail + notes; this is the artifact reviewed at **CHECKPOINT 1**.
- **`implementation-plan.md`** (bug-planner) — per file: before/after code, exact test command, ordering; reviewed at **CHECKPOINT 2**.
- **`fix-summary.md`** (bug-fixer) — *Changes Made* (file · location · before/after · test result), *Overall Status*, *Manual Verification*, *References*.
- **`security-report.md`** (security-verifier) — per finding: severity (CRITICAL/HIGH/MEDIUM/LOW/INFO) · `file:line` · description · remediation; **report only**. *Finding strategy (so the report is non-trivial):* the fixer remediates VULN-1; the security-verifier independently re-scans the changed code, **confirms VULN-1 is remediated**, and still **reports VULN-2 (hardcoded secret) as a real MEDIUM finding** plus any defense-in-depth notes — demonstrating the agent catches issues, not just rubber-stamps. (A follow-up commit moves the secret to env per its remediation.)
- **`test-report.md`** (unit-test-generator) — tests added (file → cases), FIRST compliance notes, run result + coverage.

**Every artifact is a handoff contract (p.5):** each ends with a **`## Handoff → <next agent>`**
section giving the next agent its exact inputs + what to do — structured communication, no APIs/queues.
Artifacts are **immutable** per run (written once; later phases never edit them).

## Human Checkpoints (guide p.2 / p.4)
Two mandatory human-review gates; *"agents do research, humans make decisions."*
- **CHECKPOINT 1 — before planning.** Review `verified-rca.md`. Questions: *Is the root cause correct?
  Are we fixing the right thing? Should we proceed?* **Required: user approval to continue.**
- **CHECKPOINT 2 — before implementation.** Review `implementation-plan.md`. Questions: *Are the
  changes appropriate? Is the scope correct? Any missing edge cases?* **Required: user approval.**
- **Reconciliation with single-command:** the coordinator **pauses for approval** at each checkpoint
  (interactive). For unattended/demo runs, `--auto-approve` proceeds but **records the decision**
  (verdict + timestamp) as `CHECKPOINT-1.md` / `CHECKPOINT-2.md` in the run folder — never silently skipped.

## Run Capture & Traceability
Every pipeline invocation is captured in its own **new, timestamped run folder** (immutable history):
```
context/bugs/001/runs/run-YYYY-MM-DDTHH-MM-SSZ/    # one folder per run (immutable history)
  00-bug-researcher_log.md       00-bug-researcher_result.md
  01-research-verifier_log.md    01-research-verifier_result.md
  02-rca-analyst_log.md          02-rca-analyst_result.md
  03-rca-verifier_log.md         03-rca-verifier_result.md
  04-CHECKPOINT-1.md             # human review record (decision + reason + timestamp)
  05-bug-planner_log.md          05-bug-planner_result.md
  06-CHECKPOINT-2.md
  07-bug-fixer_log.md            07-bug-fixer_result.md
  08-security-verifier_log.md    08-security-verifier_result.md
  09-unit-test-generator_log.md  09-unit-test-generator_result.md
  manifest.json                  # run id · UTC start/end · git SHA · per-stage model · verdicts · pass/fail
  pipeline-run.log               # ordered transcript of all stages
```
- **Flat, prefixed layout (no per-agent subdirs):** a single `ls run-<ts>/` shows the whole run in
  **execution order** (checkpoints in position); `cat run-<ts>/*_result.md` replays the entire pipeline
  top-to-bottom with no directory hopping. Numeric prefix = chronological step; `_log`/`_result` = type.
- **Folder name** = `run-<UTC ISO-8601, colon-free>` → sorts chronologically, human-readable.
- **`NN-<agent>_log.md`** — *very compact, structured* decisions & reasons only, one row per decision:
  `| step | decision | reason | evidence |`. No verbose narration.
- **`NN-<agent>_result.md`** — the agent's **full, structured result** (its artifact content) **plus a
  `## Handoff → <next agent>`** section. The latest run's results are copied to the canonical
  `context/bugs/001/` paths (what HW4 grades).
- **Self-documenting** filenames (step + agent + type) and **immutable** runs (new run = new folder;
  prior runs never overwritten) — the guide's File-Based Protocol (p.5).

## Agent Specifications
All in `homework-4/agents/<name>.agent.md` with frontmatter `name`, `description`, `tools`, `model`.

| Agent (file) | Mode · Model | Tools (least-privilege) | Use when… | In → Out |
|---|---|---|---|---|
| `bug-coordinator` *(= run script)* | Orchestrator | — | drive stages, gates, checkpoints, run folders | context.md → orchestrates all |
| `bug-researcher` *(helper)* | Architect · **Opus** | Read, Grep, Glob *(read-only)* | document what EXISTS — locate seeded issues with file:line | context.md → codebase-research.md |
| `research-verifier` ⭐ | Architect · **Opus** | Read, Grep, Glob *(read-only)* | fact-check research vs source using the quality skill | codebase-research → verified-research.md |
| `rca-analyst` *(helper)* | Architect · **Opus** | Read, Grep, Glob *(read-only)* | derive root cause via **5 Whys** | verified-research → rca.md |
| `rca-verifier` *(helper)* | Architect · **Opus** | Read, Grep, Glob *(read-only)* | validate the root-cause analysis | rca.md → verified-rca.md |
| `bug-planner` *(helper)* | Architect · **Opus** | Read, Grep, Glob *(read-only)* | turn verified RCA into a precise before/after plan | verified-rca → implementation-plan.md |
| `bug-fixer` ⭐⭐ | Editor · **Sonnet** | Read, Edit, Write, Bash | execute the plan; run tests after each change | implementation-plan → fix-summary.md (+ src) |
| `security-verifier` ⭐⭐ | Architect · **Opus** | Read, Grep, Glob *(read-only — enforces "report only")* | security-review changed code; rate findings | fix-summary + src → security-report.md |
| `unit-test-generator` ⭐⭐⭐ | Editor · **Sonnet** | Read, Write, Bash | generate + run FIRST tests for changed code | fix-summary + src → test-report.md + tests/ |

**Graded agents = the 4 required** (research-verifier, bug-fixer, security-verifier, unit-test-generator);
the others are guide-aligned helper stages so the pipeline matches the *WORK-Agents* canonical flow.
Each agent body: role, exact inputs/outputs (paths), step list, artifact section template, success
criteria, and explicit **"never"** rules (security-verifier never edits; fixer stops on test failure).

## Skill Specifications
In `homework-4/skills/`:
- **`research-quality-measurement.md`** (Task 1.2) — defines quality **levels** (e.g. `Verified` /
  `Partially Verified` / `Unverified` with criteria) + the **template** for `verified-research.md`'s
  required sections. `research-verifier` must use it. Concise; checklist pattern.
- **`unit-tests-FIRST.md`** (Task 4.2) — defines **F**ast/**I**ndependent/**R**epeatable/
  **S**elf-validating/**T**imely as an applied checklist the generator ticks per test. Referenced by
  `unit-test-generator`.

## Single-Command Pipeline
`homework-4/run-pipeline.sh` (+ `run-pipeline.ps1`) — the **Bug Coordinator**:
1. **Preflight + new run folder:** verify repo root + `claude` CLI + app present; create
   `context/bugs/001/runs/run-<UTC>/` and start `manifest.json` (keep author `bug-context.md`; never
   mutate prior runs).
2. **Register agents + skills:** copy each `agents/<name>.agent.md` → `.claude/agents/<name>.md` and
   `skills/*` → `.claude/skills/`. Each agent's own frontmatter `model` is honored (no global override).
3. **Run stages headlessly & sequentially** (`claude -p "Use the <agent> subagent …"`, non-interactive
   permission mode + scoped `--allowedTools`; *fallback: `--append-system-prompt "$(cat …agent.md)"`*),
   writing each stage's `NN-<agent>_log.md` + `NN-<agent>_result.md` (flat) in the run folder and
   copying the canonical artifact. Order with gates + checkpoints:
   researcher → research-verifier *(gate: Quality≠Unverified)* → rca-analyst → rca-verifier
   → **CHECKPOINT 1** *(approve; `--auto-approve` records the verdict)* → bug-planner
   → **CHECKPOINT 2** → bug-fixer *(gate: baseline tests pass; reflect-and-retry on failure)*
   → security-verifier → unit-test-generator.
4. **Verify-or-fail per stage:** assert each stage's `result.md` + canonical artifact are present
   (non-empty); abort with a clear message + non-zero exit otherwise.
5. **Finalize:** write end time + all verdicts to `manifest.json`; print a summary (artifacts,
   test/coverage, security-findings count, checkpoint decisions).
> Skills "load automatically" because the coordinator registers them and each agent references its
> skill **by name**. The committed run folder (logs + results + manifest + checkpoints) is the graded
> evidence and the pipeline's traceability/visualization; anyone with Claude Code can re-run.

## Low-Level Build Tasks
1. **Scaffold** `homework-4/` structure (dirs above). **DoD:** tree matches *Expected Structure*.
2. **Build `paycli`** with the 4 seeded issues + a runnable entry point **+ the author baseline test
   suite** (`tests/test_baseline.py`). **DoD:** `python -m paycli` runs; baseline `pytest` **fails**
   on BUG-A/BUG-B pre-fix; `bandit` flags VULN-1; `API_KEY` literal present for VULN-2.
3. **Write `bug-context.md`** documenting issues + repro. **DoD:** all 4 issues described with repro.
4. **Author the 2 skills.** **DoD:** valid frontmatter; levels/checklists defined; < 500 lines.
5. **Author the 8 agents** — Architect (read-only, Opus): researcher, research-verifier, rca-analyst,
   rca-verifier, planner, security-verifier; Editor (write, Sonnet): bug-fixer, unit-test-generator.
   **DoD:** each has model + least-privilege tools + references its skill (where applicable); read-only
   agents have no write tools; each body ends with a `## Handoff → <next agent>` template.
6. **Write `run-pipeline.sh` + `.ps1` (Bug Coordinator).** **DoD:** one command creates a timestamped
   run folder, runs all stages with **gates + 2 human checkpoints**, registers skills, and writes
   per-agent `log.md`/`result.md` + `manifest.json`.
7. **Run the pipeline for real**; capture the run folder. **DoD:** `runs/run-<UTC>/` exists with each
   stage's `log.md`+`result.md`, both `CHECKPOINT-*.md`, `manifest.json`, `pipeline-run.log`; canonical
   artifacts (incl. `rca.md`, `verified-rca.md`) produced; bugs fixed; a generated test asserts the
   **VULN-1 injection is blocked**; `security-report.md` shows VULN-1/2 remediated; `test-report.md` green.
8. **Quality gate** on fixed app, then **run `verify.sh`** (TEST_PLAN Layer A + scriptable Layer B). **DoD:** ruff/mypy/bandit/radon/pytest(≥90%) all green; `bandit` now clean; **all P0 checks in TEST_PLAN pass**.
9. **Capture screenshots** (pipeline run, fixes, security scan, unit tests) → `docs/screenshots/`.
10. **Write README + HOWTORUN + (recommended) CLAUDE.md** — README incl. **Mermaid diagram**, model
    table, "4 required + 2 helper" note, task-coverage table. **DoD:** both complete; author name present.
11. **Commit** `PLAN.md`, `TEST_PLAN.md`, `verify.sh`, agents/, skills/, context/ (incl. `pipeline-run.log`), src/, tests/, docs/, run scripts, README/HOWTORUN/CLAUDE.md.
12. **Open/Update PR** with summary + **embedded** screenshots + task-coverage table.

## Edge Cases & Failure Modes
| # | Scenario | Handling |
|---|----------|----------|
| E1 | Research quality `Unverified` | pipeline gate stops before planning; verified-research records why |
| E2 | A fix breaks tests | fixer documents failure in fix-summary and stops (no further changes) |
| E3 | Security-verifier tempted to edit | tool scope forbids Edit/Write → it can only report |
| E4 | Re-run pipeline | preflight resets prior outputs so artifacts are regenerated cleanly |
| E5 | `claude` CLI missing / non-interactive | run script fails fast with a clear message |
| E6 | Test generator covers unchanged code | skill + agent constrain to changed files only |
| E7 | Human rejects at a checkpoint | pipeline stops; rejection + reason recorded in `CHECKPOINT-*.md`; no downstream stage runs |
| E8 | RCA `5 Whys` unsound | rca-verifier marks `verified-rca` fail → gate stops before CP1/planning |

## Verification
| Requirement | How verified |
|-------------|--------------|
| M1 verified-research sections + quality | open file; checklist of 5 sections + level present; spot-check a file:line |
| M2 fixes + tests | `fix-summary.md` before/after; `pytest` green; bugs no longer reproduce |
| M3 security report | each finding has severity+file:line+remediation; `bandit` clean post-fix |
| M4 FIRST tests | `test-report.md`; tests run; coverage ≥ 90%; FIRST checklist ticked |
| M5 before/after | `bug-context.md` repro steps fail pre-fix, pass post-fix |
| M6 one command | fresh `./run-pipeline.sh` reproduces all artifacts |
| M7 models | grep each `*.agent.md` for `model:`; README justification table present |
| M8 PR/docs | README author+tables; HOWTORUN steps; PR has embedded screenshots |
| RCA | `rca.md` has a 5-Whys chain per issue; `verified-rca.md` validates each |
| Checkpoints | `CHECKPOINT-1.md`/`CHECKPOINT-2.md` record a decision; pipeline pauses or logs `--auto-approve` |
| Run capture | `runs/run-<UTC>/` has per-agent `log.md`+`result.md` + `manifest.json`; a re-run adds a new folder (prior unchanged) |
| Architect/Editor | read-only agents = Opus; write agents = Sonnet (frontmatter) |

## PR & Submission Plan
- **README** (`homework-4/README.md`): title + `**Author:** Anton Tsiatsko`; what it is; a **Mermaid
  pipeline diagram** (Alexey responded well to the Mermaid diagrams in HW2); how to run (one command)
  + how to run the app; **per-agent model table with justification**; an explicit note that there
  are **4 required graded agents + 2 helper stages** (researcher, planner); **Task → Deliverable →
  Evidence(screenshot)** coverage table; quality-gate results.
- **`CLAUDE.md`** (recommended, matches the accepted reference submission): concise project rules for
  the pipeline (stack, report-only/least-privilege, fail-on-test-failure, no-secrets).
- **HOWTORUN.md:** numbered setup → run pipeline → inspect artifacts → run app/tests.
- **Screenshots** (`docs/screenshots/`, **embedded in the PR body as images, not links**):
  `pipeline-run.png`, `fixes-applied.png`, `security-scan.png`, `unit-tests.png`. Embed via the
  branch raw URL while the PR is open; if the branch is later deleted, repoint to commit-pinned URLs.
- **PR description:** summary, the coverage table, **embedded screenshots**, link to artifacts.
- **PR target:** `atsiatsko_home_work_4` → `main` (consistent with HW1–HW3).

### Alexey-Popov 1000%-satisfaction checklist (pre-empting PR #1–#3)
- [ ] Screenshots **embedded in the PR description** (actual images, not links) — pipeline/fixes/security/tests
- [ ] **Author name** in README
- [ ] **Task-by-task coverage** table (he reviews per task; says "Task requirements are done")
- [ ] **Proper README** + **HOWTORUN**
- [ ] **Exact expected structure** incl. `run-pipeline.sh` **and** `.ps1`, committed `context/bugs/001/` artifacts
- [ ] **Single-command** run proven by screenshot
- [ ] **Models justified** per agent
- [ ] Quality gate green; no secrets in committed code; no stale placeholders

## Traceability Matrix
| HW4 item | Plan section | Deliverable(s) | Verification | Screenshot |
|----------|--------------|----------------|--------------|------------|
| Task 1 Research Verifier | Agent Specs · M1 | `agents/research-verifier.agent.md`, `verified-research.md` | M1 | security/run shots |
| Task 1.2 quality skill | Skill Specs | `skills/research-quality-measurement.md` | M1 | run |
| Task 2 Bug Fixer | Agent Specs · M2 | `agents/bug-fixer.agent.md`, `fix-summary.md`, edited `src/` | M2 | fixes-applied |
| Task 3 Security Verifier | Agent Specs · M3 | `agents/security-verifier.agent.md`, `security-report.md` | M3 | security-scan |
| Task 4 Test Generator | Agent Specs · M4 | `agents/unit-test-generator.agent.md`, `tests/`, `test-report.md` | M4 | unit-tests |
| Task 4.2 FIRST skill | Skill Specs | `skills/unit-tests-FIRST.md` | M4 | unit-tests |
| Task 5 Sample app | Sample App | `src/paycli/*`, `bug-context.md` | M5 | pipeline-run |
| Single-command | Single-Command Pipeline · M6 | `run-pipeline.sh`, `.ps1` | M6 | pipeline-run |
| Model per agent | AI-Usage · M7 | frontmatter + README table | M7 | — |
| Guide: Architect/Editor split | AI-Usage | read-only=Opus, write=Sonnet | Architect/Editor | — |
| Guide: RCA (5 Whys) | Agent/Artifact Specs | `rca.md`, `verified-rca.md` + agents | RCA | run |
| Guide: human checkpoints | Human Checkpoints | `CHECKPOINT-1/2.md` | Checkpoints | checkpoint shot |
| Guide: run capture / traceability | Run Capture & Traceability | `runs/run-<UTC>/` (logs+results+manifest) | Run capture | run |
| Screenshots/README/PR | PR & Submission · M8 | README, HOWTORUN, docs/screenshots, PR | M8 | all |
