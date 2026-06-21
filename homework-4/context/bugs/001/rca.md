# RCA Analyst Result — paycli (batch 001)

**Run:** run-2026-06-21T19-34-27Z
**Mode:** Architect (read-only). Technique: 5 Whys.
**Inputs:** `context/bugs/001/verified-research.md` (Research Quality: **Verified**),
`context/bugs/001/research/codebase-research.md`, `context/bugs/001/bug-context.md`,
source `src/paycli/transactions.py`, `src/paycli/report.py`.

## 0. Scope note (read first)

The research-verifier confirmed (Verified) that all four seeded defects are **absent** from the
current working tree — each location holds the already-remediated form. The 5-Whys chains below
therefore analyse **why each seeded defect existed in the baseline** (`bug-context.md`, commit
`08dfb7f`), which is the actionable root-cause question. Each chain ends with the **current state**
so downstream planning can decide *no-op (already remediated)* vs. *re-run against baseline*. Output
is root cause only — no fixes proposed (that is the planner's job).

There is also a **process-level** finding (Issue 5) about the tension between fixed code and the
"do not pre-fix" docstrings; it has its own chain.

---

## Issue BUG-A — boundary off-by-one in `is_within_daily_limit`

**Symptom:** `python -m paycli check-limit 60 40 100` prints `False`; a spend landing exactly on the
limit is wrongly rejected (`pytest -k limit_exactly` fails). Seed location:
`transactions.is_within_daily_limit`.

| # | Question | Answer |
|---|----------|--------|
| Symptom | What is observed? | Spend exactly at the limit is rejected (`False` instead of `True`). |
| Why 1 | Why is it rejected? | The comparison used strict `spent + amount < limit` instead of `<= limit`. |
| Why 2 | Why was strict `<` chosen? | The exact-limit boundary was implicitly treated as "over limit." |
| Why 3 | Why was the boundary treated that way? | "Within limit" was never specified as inclusive vs. exclusive of the limit value. |
| Why 4 | Why was the inclusivity unspecified? | No boundary / equivalence-partition test asserted the exact-limit case, so the ambiguity was never forced to a decision. |
| Why 5 | Why was that test missing? | No test-first discipline requiring boundary values to be enumerated before implementing the comparison. |

**Root Cause:** The inclusive upper-boundary contract for "within the daily limit" was never specified
or test-enforced, so an off-by-one choice of comparison operator (`<` vs `<=`) went undetected.

**Current state:** Remediated — `transactions.py:29` reads `return spent + amount <= limit` (inclusive).

---

## Issue BUG-B — unguarded division in `average_transaction`

**Symptom:** `python -m paycli average` (no amounts) raises `ZeroDivisionError`
(`pytest -k average_of_empty` fails). Seed location: `transactions.average_transaction`.

| # | Question | Answer |
|---|----------|--------|
| Symptom | What is observed? | Averaging an empty input crashes with `ZeroDivisionError`. |
| Why 1 | Why does it crash? | It computes `sum(amounts) / len(amounts)` with no check for `len == 0`. |
| Why 2 | Why is there no check? | The empty-sequence case was not handled before dividing. |
| Why 3 | Why was the empty case not handled? | The function's contract for empty input ("average of nothing") was undefined — no chosen return value. |
| Why 4 | Why was the contract undefined? | No edge-case test exercised empty input, so the gap never surfaced. |
| Why 5 | Why was that edge case omitted? | Degenerate-input handling was not part of the function-design / TDD checklist. |

**Root Cause:** Behavior for the empty-input edge case was neither defined nor tested; the happy-path
implementation divided by a length that can be zero.

**Current state:** Remediated — `transactions.py:19-21` guards with `if not amounts: return 0.0`.

---

## Issue VULN-1 — command injection in `export_report` (HIGH / bandit B602)

**Symptom:** `python -m paycli export "x; touch pwned.txt"` creates `pwned.txt`; `bandit -r src`
flags B602. Seed location: `report.export_report`.

| # | Question | Answer |
|---|----------|--------|
| Symptom | What is observed? | A shell metacharacter in the `path` argument executes arbitrary commands. |
| Why 1 | Why does it execute? | The user `path` was interpolated into a command string run via `subprocess.call(f"cat {path} …", shell=True)`. |
| Why 2 | Why was the input interpolated into a shell string? | Untrusted input was treated as trusted and concatenated directly. |
| Why 3 | Why was a shell used at all? | A shell was invoked to perform a plain file copy that needs no shell. |
| Why 4 | Why was the wrong tool chosen? | The developer reached for a familiar `shell=True` idiom instead of the safe library API (file I/O / argv list) and assumed no malicious input. |
| Why 5 | Why was that not caught? | No input-trust boundary / threat model for caller-supplied paths, and no SAST (bandit) gate in the workflow to flag `shell=True`. |

**Root Cause:** Untrusted input was passed through a shell because the design lacked an input-trust
boundary and a security-lint gate; a shell was used for a task (file copy) that never required one.

**Current state:** Remediated — `report.py:22-27` uses `open(...)` + `shutil.copyfileobj`; no
`subprocess` import, no `shell=True`.

---

## Issue VULN-2 — hardcoded secret `report.API_KEY` (MEDIUM)

**Symptom:** An API-key secret literal is visible in `src/paycli/report.py`. Seed location:
`report.API_KEY`.

| # | Question | Answer |
|---|----------|--------|
| Symptom | What is observed? | A secret value is committed in source as a string literal. |
| Why 1 | Why is the secret in source? | `API_KEY` was assigned a literal value directly in the module. |
| Why 2 | Why was a literal used? | The secret was inlined for convenience rather than externalized. |
| Why 3 | Why was it not externalized? | No mechanism (env var / secrets manager) was established for supplying configuration secrets. |
| Why 4 | Why was no mechanism established? | Secrets management was not part of the project's configuration/deployment design. |
| Why 5 | Why did the commit succeed? | No policy or pre-commit secret-scanning gate prevented committing secrets. |

**Root Cause:** Absence of a secrets-management convention (environment/config) and a commit-time
secret-scanning gate; the secret was modeled as a code constant instead of external configuration.

**Current state:** Remediated — `report.py:13` reads `API_KEY = os.environ.get("PAYCLI_API_KEY", "")`.

---

## Issue PROC-1 — stale "do not pre-fix" docstrings vs. fixed code (process)

**Symptom:** Module docstrings (`transactions.py:3-4`, `report.py:3-4`) still announce intentional
seeded bugs and "Do not pre-fix them," yet the code bodies are fully remediated — flagged by both
researcher and verifier.

| # | Question | Answer |
|---|----------|--------|
| Symptom | What is observed? | Docstrings describe seeded-bug intent while the code is already fixed; the pipeline is running over already-remediated source. |
| Why 1 | Why is there a mismatch? | The four fixes were applied (working tree shows `M` on both files) but the seed-narrating docstrings were not updated. |
| Why 2 | Why were the docstrings left stale? | The fix step changed code bodies only; the "do not pre-fix" comments were not part of the change scope. |
| Why 3 | Why was the pipeline run over fixed code? | The batch was (re-)started against the post-fix working tree rather than the seeded baseline `08dfb7f`. |
| Why 4 | Why against the post-fix tree? | No explicit precondition gate verifies the input state (seeded vs. remediated) before the pipeline starts. |
| Why 5 | Why is there no precondition gate? | The pipeline assumes its starting commit contains the live defects; that assumption is unstated and unchecked. |

**Root Cause:** The pipeline has no entry-state precondition check, so it ran against
already-remediated source while seed-intent docstrings stayed stale — producing a research/code
disagreement that is a process artifact, not a live defect.

**Current state:** Open as a process decision (see Handoff). Not a code defect in `paycli` logic.

---

## Summary

| Issue | Root Cause (one line) | Current code state |
|-------|-----------------------|--------------------|
| BUG-A | Inclusive upper-boundary contract unspecified & untested → wrong comparison operator. | Remediated (`<=`). |
| BUG-B | Empty-input behavior undefined & untested → division by zero. | Remediated (empty guard). |
| VULN-1 | No input-trust boundary / SAST gate → untrusted path through `shell=True`. | Remediated (file I/O). |
| VULN-2 | No secrets-management convention / secret-scan gate → literal in source. | Remediated (env var). |
| PROC-1 | No pipeline entry-state precondition → run over already-fixed code; stale docstrings. | Open (process). |

## Handoff → rca-verifier

Validate each 5-Whys chain above for logical soundness (each *Why* must actually cause the line
above it) and evidence (root cause traceable to `bug-context.md` seed and/or current source). Key
points to check:

1. **BUG-A / BUG-B / VULN-1 / VULN-2** — chains analyse the *seeded* defect's root cause; confirm
   each chain's symptom and pre-fix mechanism match `bug-context.md` rows, and that the "current
   state" line matches the verified source (`transactions.py:19-21,29`; `report.py:13,22-27`).
2. **PROC-1** — confirm this is a process/precondition root cause, not a `paycli` logic defect, and
   that it is consistent with the researcher's and verifier's notes about stale docstrings and the
   `08dfb7f` baseline.
3. **Carry-forward decision for the human checkpoint (before planning):** because all four code
   defects are already remediated, RCA → plan → fix should record **"no-op: already remediated"**
   *unless* the goal is to remediate the seeded baseline — in which case re-run against commit
   `08dfb7f` (or revert the staged changes) before planning. This is a process decision, not an RCA
   failure.
