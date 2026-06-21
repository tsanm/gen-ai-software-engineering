# Bug Fixer Result

## Changes Made

### Change 1 — BUG-A: inclusive daily-limit boundary

**File:** `src/paycli/transactions.py` — `is_within_daily_limit()` (line 29)

**Before:**
```python
return spent + amount < limit
```

**After:**
```python
return spent + amount <= limit
```

**Docstring updated:** Removed the bug description; now reads "A spend that lands exactly on `limit` is allowed (inclusive upper bound)."

**Test result after this change:** 5 passed, 1 failed (`test_average_of_empty_is_zero` — BUG-B, not yet fixed at this step, expected).

---

### Change 2 — BUG-B: guard empty sequence in average

**File:** `src/paycli/transactions.py` — `average_transaction()` (line 17-21)

**Before:**
```python
def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount.

    BUG-B: divides by ``len`` with no guard for an empty sequence, so an empty
    input raises ``ZeroDivisionError`` instead of returning 0.
    """
    return sum(amounts) / len(amounts)
```

**After:**
```python
def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount; 0.0 for an empty sequence."""
    if not amounts:
        return 0.0
    return sum(amounts) / len(amounts)
```

**Test result after this change:** 6 passed, 0 failed.

---

### Change 3 — VULN-1: remove `shell=True` command injection

**File:** `src/paycli/report.py` — imports + `export_report()`

**Before (import):**
```python
import subprocess
```

**After (import):**
```python
import shutil
```

**Before (function):**
```python
def export_report(path: str) -> int:
    """Concatenate the file at ``path`` into ``report.txt``.

    VULN-1: builds a shell command from caller-supplied input with ``shell=True``,
    enabling command injection (e.g. ``path = "x; rm -rf ."``).
    """
    return subprocess.call(f"cat {path} > report.txt", shell=True)
```

**After (function):**
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

**Test result after this change:** 6 passed, 0 failed.

---

### Change 4 — VULN-2: move hardcoded secret to env var

**File:** `src/paycli/report.py` — imports + module-level `API_KEY`

**Before (import block):**
```python
import shutil
```

**After (import block):**
```python
import os
import shutil
```

**Before (constant):**
```python
# VULN-2: hardcoded secret committed in source (fake value, for the security agent to flag).
API_KEY = "sk-live-DEMO0000000000000000000000"
```

**After (constant):**
```python
# API key is read from the environment, never committed to source.
API_KEY = os.environ.get("PAYCLI_API_KEY", "")
```

**Test result after this change:** 6 passed, 0 failed.

---

## Overall Status

**ALL CHANGES APPLIED SUCCESSFULLY — ALL TESTS PASS**

- 4/4 changes applied exactly as planned
- 6/6 baseline tests pass after all changes
- No test failures at any step (Change 1's 1 failing test was the not-yet-fixed BUG-B, which resolved in Change 2)

Full quality-gate run: `6 passed` in `tests/` with `-q` flag.

---

## Manual Verification

```bash
# Verify all baseline tests pass
.venv/bin/python -m pytest tests/ -v

# Confirm BUG-A fix: exact-limit spend is now accepted
python -c "from src.paycli.transactions import is_within_daily_limit; print(is_within_daily_limit(90.0, 10.0, 100.0))"
# Expected: True

# Confirm BUG-B fix: empty sequence returns 0.0 without error
python -c "from src.paycli.transactions import average_transaction; print(average_transaction([]))"
# Expected: 0.0

# Confirm VULN-1 fix: no shell=True, uses file I/O
python -c "import inspect, src.paycli.report as r; print('shell=True' not in inspect.getsource(r.export_report))"
# Expected: True

# Confirm VULN-2 fix: no hardcoded secret, reads from env
python -c "from src.paycli.report import API_KEY; print(repr(API_KEY))"
# Expected: '' (or whatever PAYCLI_API_KEY env var is set to)

# Set env var and verify it is picked up
PAYCLI_API_KEY=test-key python -c "from src.paycli.report import API_KEY; print(API_KEY)"
# Expected: test-key (note: env var must be set before import due to module-level eval)
```

---

## References

- Implementation plan: `context/bugs/001/implementation-plan.md`
- RCA: `context/bugs/001/rca.md`
- Verified RCA: `context/bugs/001/verified-rca.md`

---

## Handoff → security-verifier

The following files were modified and are ready for security review:

1. `src/paycli/transactions.py` — BUG-A and BUG-B fixes (logic only, no security impact)
2. `src/paycli/report.py` — VULN-1 (shell injection removed) and VULN-2 (hardcoded secret removed)

Security review should focus on `src/paycli/report.py`:
- `export_report()`: confirm `shell=True` is gone and the new file-I/O path cannot be exploited
- `API_KEY`: confirm the literal string `sk-live-DEMO0000000000000000000000` no longer appears anywhere in source
