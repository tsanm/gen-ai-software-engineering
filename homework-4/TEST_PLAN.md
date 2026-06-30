# Homework 4 — Test Plan & Suite (TDD-first)

> The acceptance contract for HW4. Written **before** the build (TDD): the software tests start
> **red** (fail on the seeded bugs) and the pipeline must turn them **green**; the deliverable checks
> are the acceptance gate. **Ship only when every P0 passes.** Authored from a Staff AI-QA + reviewer
> (Alexey-Popov) perspective. Each check is a single, unambiguous, executable assertion.

**Status:** Aligned to Alexey-Popov's *WORK-Agents* guide · **Version:** 2.0 · **Author:** Anton Tsiatsko ·
**Date:** 2026-06-21 · **Scope:** `homework-4/` · Pairs with [`PLAN.md`](PLAN.md).

## Definitions (binding — every check uses these exact meanings)
- **PASS / FAIL** — a check PASSES iff its *Pass criteria* is met verbatim; otherwise FAIL.
- **P0** — *blocking*: any FAIL means HW4 is incorrect/incomplete or will fail review → must not ship.
- **P1** — *quality*: a FAIL is a recorded defect; ship only with explicit written waiver.
- **present** — the file exists at the stated path **and** is non-empty (size > 0 bytes).
- **pre-fix** — repository state at `git` tag/stash before the bug-fixer stage runs.
- **post-fix** — state after the full pipeline run completes.
- **fixed** — a baseline test that FAILED pre-fix PASSES post-fix, with no other baseline test regressing.
- **read-only agent** — its frontmatter `tools` list contains **none** of `Edit`, `Write`, `Bash`.
- **clean (tool)** — the tool exits 0 with zero reported findings at the stated severity.
- **resolves (file:line)** — the cited file exists and the cited line number is ≤ the file's line count.
- **embedded screenshot** — appears in the PR body as a Markdown image `![alt](url)` whose `url`
  returns HTTP 200; a bare hyperlink `[text](url)` does **not** count.
- **graded agents** — the 4 required: research-verifier, bug-fixer, security-verifier, unit-test-generator.

## Test strategy
- **Two layers:** **(A) Software tests** — `pytest` over `paycli` (functional correctness, TDD red→green);
  **(B) Deliverable/process checks** — file/format/PR assertions (mostly scriptable via `grep`/`test`/`gh`).
- **Test design technique (minimal yet complete):** **Boundary-Value Analysis + Equivalence
  Partitioning** for single-factor functions; **pairwise (all-pairs)** only where a function has ≥2
  independent factors (see *Functional Test Matrix*). This maximizes defect coverage per case.
- **Automation:** Layer A and most of Layer B run from one command (`verify.sh`, see *Exit Criteria*);
  PR-body checks (C4) are run against the live PR via `gh`.
- **Evidence:** every PASS is backed by command output or a named file — never by assertion alone.

---

## Task 1 — Bug Research Verifier (+ skill 1.2)
| ID | Pri | Check (assertion) | Method | Pass criteria |
|----|-----|-------------------|--------|---------------|
| T1-P0-01 | P0 | `agents/research-verifier.agent.md` is present | `test -s` | true |
| T1-P0-02 | P0 | Its frontmatter has all of `name`,`description`,`tools`,`model` | parse YAML | 4 keys present |
| T1-P0-03 | P0 | `model` is the stronger-reasoning tier (an `opus` id) | grep `model:` | value contains `opus` |
| T1-P0-04 | P0 | Agent is **read-only** | parse `tools` | no Edit/Write/Bash |
| T1-P0-05 | P0 | Body references skill `research-quality-measurement` by name | grep | ≥1 match |
| T1-P0-06 | P0 | `skills/research-quality-measurement.md` present, valid frontmatter | parse | `name` matches `^[a-z0-9-]{1,64}$`, no `claude`/`anthropic`; `description` non-empty |
| T1-P0-07 | P0 | Skill defines ≥2 named quality levels, each with explicit criteria | inspect | ≥2 levels + criteria text |
| T1-P0-08 | P0 | `context/bugs/001/research/verified-research.md` present with the 5 required headings | grep headings | all of: Verification Summary, Verified Claims, Discrepancies Found, Research Quality Assessment, References |
| T1-P0-09 | P0 | Verification Summary states pass/fail **and** a Research Quality level from the skill vocabulary | inspect | both present; level ∈ skill levels |
| T1-P0-10 | P0 | Every `file:line` in verified-research.md **resolves** | script | 100% resolve; 0 dangling |
| T1-P1-01 | P1 | Description is third-person and contains a "Use when" trigger | inspect | true |
| T1-P1-02 | P1 | Research Quality Assessment gives ≥1 sentence of reasoning | inspect | true |
| T1-P1-03 | P1 | Discrepancies Found is explicit even when none (states "None") | inspect | true |
| T1-P1-04 | P1 | verified-research.md cites `codebase-research.md` (chain continuity) | grep | ≥1 match |
| T1-P1-05 | P1 | Skill body < 500 lines, references one level deep | `wc -l` + inspect | true |

## Task 2 — Bug Fixer
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| T2-P0-01 | P0 | `agents/bug-fixer.agent.md` present | `test -s` | true |
| T2-P0-02 | P0 | Frontmatter has `name`,`description`,`tools`,`model` | parse | 4 keys |
| T2-P0-03 | P0 | `tools` include `Edit`,`Write`,`Bash` (can change code + run tests) | parse | all 3 present |
| T2-P0-04 | P0 | `context/bugs/001/fix-summary.md` present with 4 required headings | grep | Changes Made, Overall Status, Manual Verification, References |
| T2-P0-05 | P0 | Each "Changes Made" entry has file · location · before/after · test result | inspect | all 4 fields per entry |
| T2-P0-06 | P0 | **BUG-A fixed**: spend exactly at limit is allowed | `pytest -k limit_boundary` | exit 0 |
| T2-P0-07 | P0 | **BUG-B fixed**: empty input returns 0, raises nothing | `pytest -k empty` | exit 0 |
| T2-P0-08 | P0 | Baseline suite that failed pre-fix now **passes** post-fix | run baseline pre vs post | pre: ≥1 fail; post: 0 fail |
| T2-P0-09 | P0 | "Overall Status" matches the actual post-fix test result | cross-check | status == real result |
| T2-P0-10 | P0 | No baseline test regressed | `pytest` | 0 unexpected failures |
| T2-P1-01 | P1 | Before/after blocks cite resolving file:line | script | true |
| T2-P1-02 | P1 | Manual Verification lists concrete commands | inspect | ≥1 runnable command |
| T2-P1-03 | P1 | Agent body states the "stop on test failure" rule | grep | match |
| T2-P1-04 | P1 | References link to `implementation-plan.md` | grep | match |

## Task 3 — Security Vulnerabilities Verifier
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| T3-P0-01 | P0 | `agents/security-verifier.agent.md` present | `test -s` | true |
| T3-P0-02 | P0 | Frontmatter has `name`,`description`,`tools`,`model` | parse | 4 keys |
| T3-P0-03 | P0 | `model` is stronger-reasoning (`opus`) | grep | contains `opus` |
| T3-P0-04 | P0 | Agent is **read-only** (enforces "report only") | parse `tools` | no Edit/Write/Bash |
| T3-P0-05 | P0 | `context/bugs/001/security-report.md` present | `test -s` | true |
| T3-P0-06 | P0 | Every finding has severity ∈ {CRITICAL,HIGH,MEDIUM,LOW,INFO} + file:line + remediation | inspect | all 3 per finding |
| T3-P0-07 | P0 | Report addresses VULN-1 (command injection in `report.export_report`) | grep | reference present |
| T3-P0-08 | P0 | Security stage edits no source: `src/` tree hash identical immediately before and after the stage | `find src -type f -print0 \| xargs -0 sha256sum` pre vs post stage | hashes equal |
| T3-P0-09 | P0 | Post-fix `bandit` over `src/` reports no HIGH/CRITICAL | `bandit -r src` | 0 HIGH/CRITICAL |
| T3-P1-01 | P1 | Report confirms VULN-1 is remediated post-fix | inspect | statement present |
| T3-P1-02 | P1 | Report contains ≥1 non-trivial finding (e.g. VULN-2 secret), not "all clear" | inspect | ≥1 finding |
| T3-P1-03 | P1 | Findings ordered by descending severity | inspect | ordered |
| T3-P1-04 | P1 | Remediations are specific (name the fix), not generic | inspect | true |

## Task 4 — Unit Test Generator (+ skill 4.2)
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| T4-P0-01 | P0 | `agents/unit-test-generator.agent.md` present | `test -s` | true |
| T4-P0-02 | P0 | Frontmatter has `name`,`description`,`tools`,`model` | parse | 4 keys |
| T4-P0-03 | P0 | `tools` include `Write` and `Bash` (generate + run) | parse | both present |
| T4-P0-04 | P0 | Body references skill `unit-tests-FIRST` by name | grep | ≥1 match |
| T4-P0-05 | P0 | `skills/unit-tests-FIRST.md` present and defines all 5 FIRST letters | grep | Fast, Independent, Repeatable, Self-validating, Timely all present |
| T4-P0-06 | P0 | `tests/` contains ≥1 generated test file for changed code | inspect | present |
| T4-P0-07 | P0 | Generated + baseline tests run and pass | `pytest` | exit 0 |
| T4-P0-08 | P0 | `context/bugs/001/test-report.md` present (tests added + result + coverage) | inspect | all 3 |
| T4-P0-09 | P0 | Coverage on `src/paycli/` ≥ 90% | `pytest --cov=src/paycli --cov-fail-under=90` | exit 0 |
| T4-P0-10 | P0 | Generated tests target changed code (BUG-A/B, VULN-1 fix) | inspect names/targets | each maps to a fix |
| T4-P1-01 | P1 | test-report records FIRST compliance per added test | inspect | true |
| T4-P1-02 | P1 | Tests are **Independent** (pass under `pytest -p no:randomly`/random order) | run shuffled | exit 0 |
| T4-P1-03 | P1 | Tests are **Self-validating** (every test has ≥1 assert; no manual step) | inspect/grep `assert` | true |
| T4-P1-04 | P1 | Generated tests do not duplicate baseline cases | inspect | no duplicates |

## Task 5 — Sample Mini Application
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| T5-P0-01 | P0 | `src/paycli/` present with a runnable entry point | `python -m paycli --help` | exit 0 |
| T5-P0-02 | P0 | ≥2 intentional bugs exist (BUG-A, BUG-B) | inspect code | both present pre-fix |
| T5-P0-03 | P0 | ≥1 intentional security issue exists (VULN-1) | inspect code | present pre-fix |
| T5-P0-04 | P0 | `context/bugs/001/bug-context.md` documents each issue with reproduction | inspect | repro per issue |
| T5-P0-05 | P0 | A test command works | `pytest -q` | runs (collects ≥1) |
| T5-P0-06 | P0 | **Pre-fix**: baseline FAILS on BUG-A and BUG-B | run on pre-fix | ≥2 failures |
| T5-P0-07 | P0 | **Pre-fix**: `bandit` flags VULN-1 | `bandit -r src` pre-fix | ≥1 HIGH (shell injection) |
| T5-P0-08 | P0 | **Post-fix**: app runs; bugs resolved; tests pass | run | exit 0 |
| T5-P0-09 | P0 | Stack is single-language, deps declared | inspect `pyproject.toml` | Python only; deps listed |
| T5-P1-01 | P1 | App is small enough to fix in one run (core ≤ ~300 LOC) | `wc -l src/paycli/*.py` | ≤ 300 |
| T5-P1-02 | P1 | App README/section documents run + test commands | grep | both |
| T5-P1-03 | P1 | Post-fix money paths use `Decimal`/minor units (no `float`) | grep `float(` in money fns | 0 |
| T5-P1-04 | P1 | Pipeline artifacts reference real files in this app | = T1-P0-10 | resolve |

## Cross-cutting C1 — Single-command pipeline / E2E
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| E2E-P0-01 | P0 | `run-pipeline.sh` present and executable; `run-pipeline.ps1` present | `test -x` / `test -s` | true |
| E2E-P0-02 | P0 | One command runs **all 8 agent stages + 2 checkpoints in order** | run / inspect | order matches PLAN |
| E2E-P0-03 | P0 | Skills auto-load (no manual per-agent skill loading) | inspect | registration step present |
| E2E-P0-04 | P0 | One run produces **all 9** canonical `context/bugs/001/` artifacts (incl. `rca.md`, `verified-rca.md`) | run → file checks | 9/9 present |
| E2E-P0-05 | P0 | Gates enforced (stop on Unverified research / failed fixer tests) | inspect | gate logic present |
| E2E-P0-06 | P0 | No manual per-agent invocation between steps | inspect | single entry point |
| E2E-P1-01 | P1 | Re-run resets and regenerates artifacts cleanly (idempotent) | run twice | identical structure |
| E2E-P1-02 | P1 | Fails fast with clear message if `claude` CLI absent | simulate | non-zero + message |
| E2E-P1-03 | P1 | Prints an end-of-run summary | run | summary present |

## Cross-cutting C2 — AI-usage excellence
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| AIU-P0-01 | P0 | All 4 graded agents present with explicit `model:` | grep | 4/4 have model |
| AIU-P0-02 | P0 | Read-only agents (research-verifier, security-verifier) have no Edit/Write/Bash | parse | true |
| AIU-P0-03 | P0 | Each agent file declares exactly one role (single responsibility) | inspect | true |
| AIU-P0-04 | P0 | README has a per-agent **model table with justification** | inspect | table present, all agents |
| AIU-P0-05 | P0 | Both skills have valid frontmatter (name regex; desc ≤1024; no reserved words) | parse | true |
| AIU-P1-01 | P1 | Agent descriptions are third-person "Use when" triggers | inspect | true |
| AIU-P1-02 | P1 | Each skill body < 500 lines, references one level deep | `wc`/inspect | true |
| AIU-P1-03 | P1 | README states "4 required + 2 helper" distinction | grep | present |

## Cross-cutting C3 — Engineering excellence (quality gate)
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| ENG-P0-01 | P0 | `ruff` clean | `ruff check` | exit 0, 0 issues |
| ENG-P0-02 | P0 | `mypy` clean | `mypy src` | exit 0 |
| ENG-P0-03 | P0 | `bandit` clean post-fix | `bandit -r src` | 0 HIGH/CRITICAL |
| ENG-P0-04 | P0 | `radon` complexity no C-or-worse | `radon cc -n C src` | empty output |
| ENG-P0-05 | P0 | `pytest` passes; coverage ≥90% on `src/paycli/` | `pytest --cov-fail-under=90` | exit 0 |
| ENG-P1-01 | P1 | `pyproject.toml` configures all gate tools (reproducible) | inspect | all configured |
| ENG-P1-02 | P1 | No secret literal in committed code post-fix | grep `sk-`/key pattern | 0 matches |
| ENG-P1-03 | P1 | No `float(` in money paths post-fix | grep | 0 matches |

## Cross-cutting C4 — PR / homework output (Alexey-Popov first-time-pass)
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| PR-P0-01 | P0 | `README.md` present and contains author "Anton Tsiatsko" | grep | match |
| PR-P0-02 | P0 | `HOWTORUN.md` present with numbered steps | inspect | ≥1 ordered list, setup→demo |
| PR-P0-03 | P0 | `docs/screenshots/` has all 4 PNGs (pipeline-run, fixes-applied, security-scan, unit-tests) | `ls` | 4/4 present |
| PR-P0-04 | P0 | PR description **embeds** ≥4 screenshots as images (not links) | inspect PR body | ≥4 `![` whose URLs return 200 |
| PR-P0-05 | P0 | PR description has a task-by-task coverage table | inspect | rows for Tasks 1–5 |
| PR-P0-06 | P0 | All deliverable dirs committed (agents/ skills/ context/ src/ tests/ docs/) | `git ls-files` | each non-empty |
| PR-P0-07 | P0 | All work under `homework-4/` (not `homework-5/`) | path check | true |
| PR-P1-01 | P1 | README has a Mermaid pipeline diagram | grep ```mermaid | present |
| PR-P1-02 | P1 | PR summary present and links to artifacts | inspect | true |
| PR-P1-03 | P1 | Embedded screenshot URLs return HTTP 200 | `curl -I` | all 200 |
| PR-P1-04 | P1 | No stale placeholders (`[Your Name]`, `TODO`, `⬜`) anywhere in homework-4 | grep | 0 matches |

---

## Gap-closure checks (from the 20-question QA/reviewer review)
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| T3-P0-09b | P0 | A test asserts the VULN-1 payload is **not executed** (no side effect) | run injection test | passes; no `pwned`/side-effect file created |
| PR-P0-08 | P0 | PR is **`atsiatsko_home_work_4` → `main`** (correct head/base) | `gh pr view --json headRefName,baseRefName` | head=atsiatsko_home_work_4, base=main |
| T3-P1-05 | P1 | VULN-1 rated **HIGH or CRITICAL** (severity correctness) | inspect security-report | severity ∈ {HIGH,CRITICAL} |
| T4-P1-05 | P1 | FIRST-**Fast** (full suite < 5s) and **Repeatable** (two runs identical result) | `time pytest` ×2 | <5s; identical pass set |
| T4-P1-06 | P1 | Every *Functional Test Matrix* row has a corresponding pytest case | map rows→tests | 1:1 |
| E2E-P1-04 | P1 | `verify.sh` present and exits 0 on a completed build | run | exit 0 |
| E2E-P1-05 | P1 | A pipeline **run log/transcript** is committed (evidence agents executed) | inspect | log present, shows all 8 stages |
| E2E-P1-06 | P1 | Re-run preserves author `bug-context.md` (not overwritten) | hash pre/post run | unchanged |
| AIU-P1-04 | P1 | Each agent `model:` is a **real Claude model id** (not invented) | check vs known ids | all valid |
| ENG-P1-04 | P1 | No real secret/PII in committed **artifacts or screenshots** | grep + visual | 0 |
| ENG-P1-05 | P1 | No absolute/user-specific paths in scripts/configs | grep `/Users/`,`/home/`,`C:\\` | 0 |
| PR-P1-05 | P1 | Each screenshot's **content matches its filename** | manual visual | true |
| PR-P1-06 | P1 | Following **HOWTORUN** reproduces app run + tests | execute the steps | succeeds |
| RES-P0-01 | P0 | `codebase-research.md` present; each seeded issue has a claim + **resolving** file:line + code snippet | inspect | all 3 per issue |
| IPL-P0-01 | P0 | `implementation-plan.md` present; per file: before/after code + exact test command + ordering | inspect | all fields present |
| RUN-P1-01 | P1 | `pipeline-run.log` committed; shows all 8 stages + 2 checkpoints executed in order | inspect | all present, ordered |

## Cross-cutting C5 — WORK-Agents guide alignment (RCA · checkpoints · run capture)
| ID | Pri | Check | Method | Pass criteria |
|----|-----|-------|--------|---------------|
| C5-P0-01 | P0 | `rca-analyst` + `rca-verifier` agent files present with full frontmatter | parse | both present; name/desc/tools/model |
| C5-P0-02 | P0 | `rca.md` present; a **5-Whys** chain per seeded issue (Symptom→Why1..5→Root Cause) | inspect | chain per issue |
| C5-P0-03 | P0 | `verified-rca.md` present; validates each RCA chain (pass/fail + notes) | inspect | verdict per chain |
| C5-P0-04 | P0 | **Architect agents** (researcher, research-verifier, rca-analyst, rca-verifier, planner, security-verifier) are **Opus + read-only** | parse | all 6: model=opus, no Edit/Write/Bash |
| C5-P0-05 | P0 | **Editor agents** (bug-fixer, unit-test-generator) are **Sonnet + write** | parse | both: model=sonnet, have write tools |
| C5-P0-06 | P0 | `04-CHECKPOINT-1.md` + `06-CHECKPOINT-2.md` present with a recorded decision (verdict + timestamp) | inspect | both present + decision |
| C5-P0-07 | P0 | Run folder `runs/run-<UTC>/` exists; name is timestamped & sortable | `ls` | matches `run-\d{4}-\d2-\d2T...` |
| C5-P0-08 | P0 | Each of the 8 stages has `NN-<agent>_log.md` + `NN-<agent>_result.md` (flat) | `ls` | 8×(log+result) present |
| C5-P0-09 | P0 | Each `_log.md` is **compact & structured** (decision/reason rows; no prose dump) | inspect | table rows; ≤ ~40 lines |
| C5-P0-10 | P0 | Each `_result.md` (except last) ends with a `## Handoff → <next>` section | grep | present per stage |
| C5-P1-01 | P1 | `manifest.json` present: run id, UTC start/end, per-stage model, verdicts | parse | fields present |
| C5-P1-02 | P1 | **Immutability**: a 2nd run creates a new folder; 1st run's files byte-identical after | hash pre/post | unchanged |
| C5-P1-03 | P1 | **Reflection**: on an induced test failure, bug-fixer iterates (retry visible), not blind-continue | inspect log | retry/reflection shown |
| C5-P1-04 | P1 | Checkpoint files address the guide's review questions | inspect | questions answered |
| C5-P1-05 | P1 | `cat run-<ts>/*_result.md` replays the pipeline in execution order (flat-layout benefit) | run | ordered, readable |

## Functional Test Matrix (Layer A — minimal, complete)
Boundary-Value + Equivalence for single-factor functions; pairwise where ≥2 factors. These are the
`pytest` cases the suite must contain (baseline + generated).

**`is_within_daily_limit(spent, amount, limit)`** — boundary (BUG-A is the "exactly" row):
| spent+amount vs limit | expected | case |
|---|---|---|
| below limit | allow (True) | EP-low |
| **exactly limit** | **allow (True)** | **BVA — BUG-A** |
| above limit | reject (False) | BVA-high |

**`average_transaction(txns)`** — equivalence partitions (BUG-B is the empty row):
| input | expected |
|---|---|
| **empty list** | **0 / Decimal(0), no exception (BUG-B)** |
| single txn | that amount |
| many txns | exact mean (Decimal) |

**`export_report(path)`** — security (VULN-1) + pairwise(path-kind × shell-metachars):
| path | expected post-fix |
|---|---|
| benign filename | report written; exit 0 |
| `"; rm -rf .` / `$(touch pwned)` | injection **not** executed; rejected or treated as literal; no side effect file created |

**Money exactness** — `Decimal` partitions: `0.10 + 0.20 == 0.30` exact; rounding HALF-EVEN at presentation only.

## Exit Criteria (Definition of Done for HW4)
- **Ship gate:** 100% of **P0** checks PASS **and** every **P1** PASS or has a written waiver in the PR.
- **One-command verify:** a `verify.sh` runs Layer A + scriptable Layer B and exits 0; C4-PR checks
  run against the live PR via `gh`. Capture its output as `docs/screenshots/unit-tests.png` evidence.
- **Pre-flight (red) proof:** before the pipeline, record that T5-P0-06/07 FAIL (bugs+vuln present);
  after, all turn PASS — this *is* the before/after evidence (M5).

## Traceability (check group → HW4 requirement)
| Check group | HW4 requirement |
|---|---|
| T1-* | Task 1 + 1.2 (research verifier + quality skill) |
| T2-* | Task 2 (bug fixer) |
| T3-* | Task 3 (security verifier, report-only) |
| T4-* | Task 4 + 4.2 (test generator + FIRST skill) |
| T5-* | Task 5 (sample app, before/after) |
| E2E-* | Overview: single-command, order, auto-load skills |
| AIU-* | Overview: explicit model per agent + best practices |
| ENG-* | Engineering excellence (quality gate) |
| PR-* | Deliverables: README/author/HOWTORUN/screenshots/PR; reviewer pass |
