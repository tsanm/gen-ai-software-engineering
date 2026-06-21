# Bug Planner Result — paycli (batch 001)

**Run:** run-2026-06-21T19-34-27Z
**Mode:** Architect (read-only). I plan; I do not edit.
**Input:** `context/bugs/001/verified-rca.md` (gate: **PASS 5/5**, open).
**Cross-checked against:** seeded baseline `08dfb7f` (defects live), working tree
`src/paycli/transactions.py` + `src/paycli/report.py` (defects already remediated),
`tests/test_baseline.py`, `context/bugs/001/bug-context.md`, `CLAUDE.md` quality gate.

## 0. Critical entry-state fact (carried from RCA)

All four **code** defects are **already remediated in the working tree** (uncommitted `M`
changes). The "before" snippets below are the live defects at baseline `08dfb7f`; the "after"
snippets are what the current source already shows. The plan therefore defines **two operating
modes** — the human picks one at CHECKPOINT 2:

- **Mode A — Verify-only (default).** Working tree already has the fixes. The bug-fixer makes
  **no code edits** for BUG-A/BUG-B/VULN-1/VULN-2; it only runs each change's **test command** to
  confirm the after-state holds. PROC-1 (docstrings) is the only real edit.
- **Mode B — Re-seed then fix.** Reset the two source files to baseline `08dfb7f` (re-introducing
  the defects), then apply the before→after changes below in order, running each test after each
  change. Use this to actually exercise the fix pipeline end-to-end.

The before/after pairs are **identical in both modes** — only the starting tree differs. PROC-1 is
pending in **both** modes.

## 1. Safe ordering of changes

1. **PROC-1** docstring cleanup (no behavior change; unblocks the "no live defects" contract).
2. **BUG-A** boundary operator (pure logic; covered by RED baseline test).
3. **BUG-B** empty-input guard (pure logic; covered by RED baseline test).
4. **VULN-2** secret externalization (do before VULN-1 so `import os` already present when editing
   `report.py`, minimizing churn / merge surface in one file).
5. **VULN-1** command-injection removal (largest rewrite in `report.py`; touches imports + body).

Rationale: logic fixes first (fastest feedback, fully test-gated), then the two `report.py`
security fixes grouped last and ordered to share the `import` edit. In Mode A every step is a
verify-only no-op except PROC-1.

---

## 2. Per-change specification (file · symbol · before · after · test)

### Change 1 — PROC-1 · stale module NOTE docstrings  **(PENDING in both modes)**

**File / symbol:** `src/paycli/transactions.py` (module docstring, L1–5) and
`src/paycli/report.py` (module docstring, L1–5).

The module-level NOTEs still assert that live seeded defects exist and must not be "pre-fixed".
The defects are remediated, so these notes are now false and must be removed.

**Before — `src/paycli/transactions.py` L1–5:**
```python
"""Core transaction logic for paycli.

NOTE: this module contains intentional seeded bugs for the pipeline to find and fix
(see context/bugs/001/bug-context.md). Do not "pre-fix" them by hand.
"""
```
**After:**
```python
"""Core transaction logic for paycli."""
```

**Before — `src/paycli/report.py` L1–5:**
```python
"""Report export for paycli.

NOTE: this module contains intentional seeded security issues for the pipeline to
find (see context/bugs/001/bug-context.md). The values/paths are demo-only.
"""
```
**After:**
```python
"""Report export for paycli."""
```

**Test command (proves the stale text is gone; expect exit 1 = no matches):**
```bash
! grep -rniE 'seeded|do not .?pre-fix|intentional' src/paycli/
```

---

### Change 2 — BUG-A · `transactions.is_within_daily_limit`

**File / symbol:** `src/paycli/transactions.py` → `is_within_daily_limit` (L24–29).
Inclusive upper-boundary contract was never test-enforced; operator was strict `<`.

**Before (baseline `08dfb7f`):**
```python
def is_within_daily_limit(spent: float, amount: float, limit: float) -> bool:
    """Return True if charging ``amount`` keeps the day's total within ``limit``.

    BUG-A: uses a strict ``<`` comparison, so a spend that lands *exactly* on the
    limit is wrongly rejected (off-by-one boundary error). Should be ``<=``.
    """
    return spent + amount < limit
```
**After (already in working tree at L24–29):**
```python
def is_within_daily_limit(spent: float, amount: float, limit: float) -> bool:
    """Return True if charging ``amount`` keeps the day's total within ``limit``.

    A spend that lands exactly on ``limit`` is allowed (inclusive upper bound).
    """
    return spent + amount <= limit
```

**Test command (RED at baseline, GREEN after):**
```bash
pytest -k "limit_exactly or limit_over or limit_under" -q
```
Spot-check: `python -m paycli check-limit 60 40 100` → `True`.

---

### Change 3 — BUG-B · `transactions.average_transaction`

**File / symbol:** `src/paycli/transactions.py` → `average_transaction` (L17–21).
Empty-input behavior undefined/untested → division by zero.

**Before (baseline `08dfb7f`):**
```python
def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount.

    BUG-B: divides by ``len`` with no guard for an empty sequence, so an empty
    input raises ``ZeroDivisionError`` instead of returning 0.
    """
    return sum(amounts) / len(amounts)
```
**After (already in working tree at L17–21):**
```python
def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount; 0.0 for an empty sequence."""
    if not amounts:
        return 0.0
    return sum(amounts) / len(amounts)
```

**Test command (RED at baseline, GREEN after):**
```bash
pytest -k "average_of_empty or average_basic" -q
```
Spot-check: `python -m paycli average` → `0` (no `ZeroDivisionError`).

---

### Change 4 — VULN-2 · `report.API_KEY` hardcoded secret (MEDIUM)

**File / symbol:** `src/paycli/report.py` → module imports + `API_KEY` (L9–13).
No secrets-management convention → literal secret committed.

**Before (baseline `08dfb7f`):**
```python
import subprocess

# VULN-2: hardcoded secret committed in source (fake value, for the security agent to flag).
API_KEY = "sk-live-DEMO0000000000000000000000"
```
**After (already in working tree; `import os` added, literal gone):**
```python
import os
import shutil

# API key is read from the environment, never committed to source.
API_KEY = os.environ.get("PAYCLI_API_KEY", "")
```

**Test command (no secret literal remains; expect exit 1 = no matches):**
```bash
! grep -rnE 'sk-live-|API_KEY *= *["'\'']' src/paycli/
```

---

### Change 5 — VULN-1 · `report.export_report` command injection (HIGH / B602)

**File / symbol:** `src/paycli/report.py` → `export_report` (L16–27).
No input-trust boundary; shell used (`shell=True`) for a task needing no shell.

**Before (baseline `08dfb7f`):**
```python
def export_report(path: str) -> int:
    """Concatenate the file at ``path`` into ``report.txt``.

    VULN-1: builds a shell command from caller-supplied input with ``shell=True``,
    enabling command injection (e.g. ``path = "x; rm -rf ."``).
    """
    return subprocess.call(f"cat {path} > report.txt", shell=True)
```
**After (already in working tree at L16–27 — plain file I/O, no shell, `subprocess` removed):**
```python
def export_report(path: str) -> int:
    """Copy the file at ``path`` into ``report.txt`` using plain file I/O.

    No shell is involved, so a caller-supplied ``path`` cannot inject commands.
    Returns 0 on success and 1 if the source path cannot be read.
    """
    try:
        with open(path, "rb") as src, open("report.txt", "wb") as dst:
            shutil.copyfileobj(src, dst)
    except OSError:
        return 1
    return 0
```

**Test commands (no HIGH from bandit; injection cannot execute):**
```bash
bandit -r src -ll          # expect: no HIGH severity / no B602
rm -f pwned.txt; python -m paycli export "x; touch pwned.txt"; test ! -e pwned.txt && echo OK
```
The unit-test-generator will add the FIRST `injection-blocked` test for this in `tests/`.

---

## 3. Full-gate verification (run once after all changes, both modes)

Per `CLAUDE.md` quality gate — all must be green to ship:
```bash
ruff check src tests
mypy src/paycli
bandit -r src -ll                 # no HIGH
radon cc -nc src/paycli           # no C-or-worse
pytest --cov=src/paycli --cov-report=term-missing --cov-fail-under=90
```

## 4. Acceptance summary

| # | ID | File:symbol | Mode A | Mode B | Proving test |
|---|----|-------------|--------|--------|--------------|
| 1 | PROC-1 | both modules: docstring | **edit** | **edit** | `! grep -rniE 'seeded\|pre-fix\|intentional' src/paycli/` |
| 2 | BUG-A | transactions:`is_within_daily_limit` | verify | edit `<`→`<=` | `pytest -k "limit_exactly or limit_over or limit_under"` |
| 3 | BUG-B | transactions:`average_transaction` | verify | edit add guard | `pytest -k "average_of_empty or average_basic"` |
| 4 | VULN-2 | report:`API_KEY` | verify | edit literal→env | `! grep -rnE 'sk-live-' src/paycli/` |
| 5 | VULN-1 | report:`export_report` | verify | edit shell→file I/O | `bandit -r src -ll`; injection probe leaves no `pwned.txt` |

## Handoff → bug-fixer

**Decision required at CHECKPOINT 2:** choose **Mode A (verify-only, default)** or **Mode B
(re-seed `08dfb7f` then apply)**. The before/after snippets above are authoritative for either.

**Do in this order:**
1. **PROC-1 (always):** remove the stale module NOTE docstrings in `transactions.py` and
   `report.py` exactly as specified. Run the grep test.
2. **Mode A:** for changes 2–5, **do not edit** — run each listed test command and record that the
   after-state already holds (RED-at-baseline tests are GREEN in the working tree).
   **Mode B:** `git checkout 08dfb7f -- src/paycli/transactions.py src/paycli/report.py`, then
   apply changes 2–5 in the order above, running each change's test immediately after.
3. **Always:** finish with the full quality gate in §3; coverage **≥ 90%** on `src/paycli/`.
4. Stop and reflect-then-retry on any failing test before continuing (Golden rule: fail on test
   failure). Hand off to **security-verifier** (report-only) once the gate is green.

**Carry-forward note for unit-test-generator:** baseline tests already cover BUG-A/BUG-B; the new
FIRST test still owed is the **VULN-1 injection-blocked** test for `export_report` — do not
duplicate the existing `test_baseline.py` cases.
