# Bug Fixer Decision Log

| step | decision | reason | evidence |
|------|----------|--------|----------|
| 1 | Read `src/paycli/transactions.py` and `src/paycli/report.py` before editing | Required by Edit tool rules; confirmed actual before-state matched plan | File contents matched plan exactly |
| 2 | Apply Change 1: `< limit` → `<= limit` in `is_within_daily_limit()` | Plan specifies inclusive boundary fix for BUG-A | Edit succeeded; `return spent + amount <= limit` now in file |
| 3 | Run `pytest tests/` after Change 1 | Required after every change per task instructions | 5 passed, 1 failed (`test_average_of_empty_is_zero`) — expected; BUG-B not yet fixed |
| 4 | Continue to Change 2 (did not stop) | The 1 remaining failure is the not-yet-fixed BUG-B; it is not a regression | Only pre-existing BUG-B test was failing; BUG-A tests now pass |
| 5 | Apply Change 2: add empty-guard `if not amounts: return 0.0` in `average_transaction()` | Plan specifies ZeroDivisionError guard for BUG-B | Edit succeeded |
| 6 | Run `pytest tests/` after Change 2 | Required after every change | 6 passed, 0 failed — all baseline tests green |
| 7 | Apply Change 3: replace `import subprocess` with `import shutil`; rewrite `export_report()` to use file I/O | Plan specifies removal of `shell=True` command injection (VULN-1) | Edit succeeded; `subprocess` removed, `shutil.copyfileobj` used |
| 8 | Run `pytest tests/` after Change 3 | Required after every change | 6 passed, 0 failed |
| 9 | Apply Change 4: add `import os`; replace hardcoded `API_KEY` literal with `os.environ.get("PAYCLI_API_KEY", "")` | Plan specifies secret must not be committed to source (VULN-2) | Edit succeeded |
| 10 | Run `pytest tests/` after Change 4 | Required after every change | 6 passed, 0 failed |
| 11 | Run full quality-gate `pytest tests/ -q` | Required as final step per plan | 6 passed, clean output |
| 12 | Write result and log artifacts to run directory | Required output per task instructions | Files written to `context/bugs/001/runs/run-2026-06-21T19-18-05Z/` |
