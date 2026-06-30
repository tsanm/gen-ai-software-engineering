# Bug Fixer — Fix Summary (batch 001)

Executed `implementation-plan.md` Changes 1–4 in order. Every change was applied as specified
(exact before→after); `pytest tests/` ran after each change; all tests passed at every checkpoint.

---

## 1. Changes Made

### Change 1 — BUG-A: inclusive daily-limit boundary

- **File:** `src/paycli/transactions.py` · `is_within_daily_limit` · line 32
- **Before:**
  ```python
      return spent + amount < limit
  ```
- **After:**
  ```python
      return spent + amount <= limit
  ```
- **Test result:** 3 passed (`test_limit_exactly_at_limit_is_allowed` flipped RED→GREEN;
  `test_limit_over_is_rejected` and `test_limit_under_is_allowed` remained GREEN).

---

### Change 2 — BUG-B: guard empty-sequence average

- **File:** `src/paycli/transactions.py` · `average_transaction` · line 23
- **Before:**
  ```python
      return sum(amounts) / len(amounts)
  ```
- **After:**
  ```python
      if not amounts:
          return 0.0
      return sum(amounts) / len(amounts)
  ```
- **Test result:** 2 passed (`test_average_of_empty_is_zero` flipped RED→GREEN;
  `test_average_basic` remained GREEN).

---

### Change 3 — VULN-2: read credential from the environment

- **File:** `src/paycli/report.py` · module-level `API_KEY` · lines 7–12
- **Before:**
  ```python
  from __future__ import annotations

  import subprocess

  # VULN-2: hardcoded secret committed in source (fake value, for the security agent to flag).
  API_KEY = "sk-live-DEMO0000000000000000000000"
  ```
- **After:**
  ```python
  from __future__ import annotations

  import os
  import shutil

  # Credential is injected from the environment; no secret is committed in source.
  API_KEY = os.environ.get("PAYCLI_API_KEY", "")
  ```
- **Verification:**
  - `python -c "import paycli.report as r; print('import ok; API_KEY empty=' + str(r.API_KEY == ''))"` → `import ok; API_KEY empty=True`
  - `grep "sk-live-DEMO" src/paycli/report.py` → 0 matches (literal removed)
- **Note:** Change 4 was applied before running tests (per plan: "do not run tests in that window
  between the two report.py edits"). Tests deferred to Change 4's test command.

---

### Change 4 — VULN-1: remove `shell=True`; no-shell file copy

- **File:** `src/paycli/report.py` · `export_report` · lines 15–21
- **Before:**
  ```python
  def export_report(path: str) -> int:
      """Concatenate the file at ``path`` into ``report.txt``.

      VULN-1: builds a shell command from caller-supplied input with ``shell=True``,
      enabling command injection (e.g. ``path = "x; rm -rf ."``).
      """
      return subprocess.call(f"cat {path} > report.txt", shell=True)
  ```
- **After:**
  ```python
  def export_report(path: str) -> int:
      """Copy the file at ``path`` into ``report.txt``.

      ``path`` is treated strictly as data: the copy uses a no-shell library call,
      so shell metacharacters in ``path`` cannot be interpreted as commands.
      Returns 0 on success and 1 if the source cannot be read.
      """
      try:
          shutil.copyfile(path, "report.txt")
      except OSError:
          return 1
      return 0
  ```
- **Functional verification:**
  - `python -m paycli export paycli_src_test.txt` → exit 0, `report.txt` written (benign copy works)
  - `python -m paycli export 'x; touch /tmp/paycli_pwned'` → exit 1 (injection string treated as literal missing path; no side effect)
- **Full baseline test result:** `pytest tests/ -v` → **12 passed** (0 failed, 0 errors)

---

## 2. Overall Status

**SUCCESS**

All 4 changes applied exactly as specified. `pytest tests/` is green at every checkpoint and at final
full run. No baseline test regressed. No changes made outside the plan.

---

## 3. Manual Verification

```bash
# From repo root: /Users/owner/src/gen-ai-software-engineering/homework-4

# 1. Full test suite green
.venv/bin/python -m pytest tests/ -v

# 2. Secret literal gone
grep -rn "sk-live-DEMO" src/

# 3. Module import + API_KEY defaults to empty
.venv/bin/python -c "import paycli.report as r; print(r.API_KEY == '')"

# 4. Benign export (exit 0)
echo "hello" > paycli_src_test.txt
.venv/bin/python -m paycli export paycli_src_test.txt; echo "exit=$?"

# 5. Injection blocked (exit 1, no side effect)
.venv/bin/python -m paycli export 'x; touch /tmp/paycli_pwned'; echo "exit=$?"
ls /tmp/paycli_pwned 2>/dev/null && echo "PWNED (FAIL)" || echo "injection blocked (PASS)"
```

---

## 4. References

- `context/bugs/001/implementation-plan.md` — the plan executed
- `src/paycli/transactions.py` — Changed by Changes 1 and 2
- `src/paycli/report.py` — Changed by Changes 3 and 4

---

## Handoff → security-verifier

All 4 changes applied and verified. Security-review the following changed files (report only —
do not edit):

- `src/paycli/transactions.py` (Changes 1, 2 — BUG-A/BUG-B logic fixes)
- `src/paycli/report.py` (Changes 3, 4 — VULN-2 credential + VULN-1 shell-injection remediation)

Key items to verify:
1. `report.py:13` — `API_KEY` now reads from `os.environ.get("PAYCLI_API_KEY", "")`. Confirm no
   hardcoded secret remains; assess whether default-empty is safe.
2. `report.py:23-27` — `export_report` now uses `shutil.copyfile`. Confirm no shell execution path
   remains and that `OSError` catch scope is appropriate (not too broad).
3. `transactions.py:34` — `<=` boundary change. No security surface; note for completeness.
4. `transactions.py:23-24` — empty-guard `return 0.0`. No security surface; note for completeness.
