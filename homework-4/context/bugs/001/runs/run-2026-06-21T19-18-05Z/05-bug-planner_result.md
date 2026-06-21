# Bug Planner Result — paycli (batch 001)

Architect mode (read-only — this stage **plans**; it does not edit). Turns the four validated
root causes in `verified-rca.md` into precise **before/after** changes, each pinned to a
`file:symbol` with an exact snippet and a **test command** that proves it. Ordering is chosen so
every change is independently verifiable and the baseline suite (`tests/test_baseline.py`) flips
RED → GREEN.

**Sources read at planning time (current content):**
- `src/paycli/transactions.py:23` → `    return sum(amounts) / len(amounts)`
- `src/paycli/transactions.py:32` → `    return spent + amount < limit`
- `src/paycli/report.py:9` → `import subprocess`
- `src/paycli/report.py:12` → `API_KEY = "sk-live-DEMO0000000000000000000000"`
- `src/paycli/report.py:21` → `    return subprocess.call(f"cat {path} > report.txt", shell=True)`
- `src/paycli/cli.py:38` → `        return export_report(args.path)` (int return contract — preserve)
- `tests/test_baseline.py` → RED-pre-fix tests for BUG-A (`test_limit_exactly_at_limit_is_allowed`)
  and BUG-B (`test_average_of_empty_is_zero`)
- `pyproject.toml` → `pytest` has `pythonpath=["src"]`; coverage `source=["paycli"]`; `bandit`
  excludes `tests`/`.venv`.

> All test commands assume the repo root as CWD with the dev extras installed
> (`pip install -e ".[dev]"`). `pytest` resolves `src/` via `pythonpath` in `pyproject.toml`.

---

## Safe ordering of changes

| # | Change | File | Why this order |
|---|--------|------|----------------|
| 1 | BUG-A `<` → `<=` | `transactions.py` | Smallest, isolated; flips one RED baseline test. |
| 2 | BUG-B empty-seq guard | `transactions.py` | Same file as #1; flips the second RED baseline test → full baseline GREEN. |
| 3 | VULN-1 drop `shell=True` | `report.py` | Behaviour-preserving rewrite; verify with bandit + functional check before touching secrets. |
| 4 | VULN-2 secret → env var | `report.py` | Same file as #3; finish report.py in one pass, re-run bandit clean. |

Rationale: group by file (transactions.py first, then report.py) to minimise context switches, and
do the two test-pinned bug fixes first so the baseline suite is GREEN before the security
hardening (which is verified by bandit, not the baseline suite).

---

## Change 1 — BUG-A: inclusive daily-limit boundary

- **File / symbol:** `src/paycli/transactions.py` → `is_within_daily_limit()` (line 32)
- **Root cause (from RCA):** inclusive "within limit" contract implemented with an exclusive `<`.

**Before**
```python
def is_within_daily_limit(spent: float, amount: float, limit: float) -> bool:
    """Return True if charging ``amount`` keeps the day's total within ``limit``.

    BUG-A: uses a strict ``<`` comparison, so a spend that lands *exactly* on the
    limit is wrongly rejected (off-by-one boundary error). Should be ``<=``.
    """
    return spent + amount < limit
```

**After**
```python
def is_within_daily_limit(spent: float, amount: float, limit: float) -> bool:
    """Return True if charging ``amount`` keeps the day's total within ``limit``.

    A spend that lands exactly on ``limit`` is allowed (inclusive upper bound).
    """
    return spent + amount <= limit
```

**Test command (proves the fix):**
```bash
python -m pytest tests/test_baseline.py::test_limit_exactly_at_limit_is_allowed \
                 tests/test_baseline.py::test_limit_over_is_rejected \
                 tests/test_baseline.py::test_limit_under_is_allowed -q
```
Expected: 3 passed. The boundary case `is_within_daily_limit(60, 40, 100)` now returns `True`;
`over` (101) still `False`.

---

## Change 2 — BUG-B: guard empty sequence in average

- **File / symbol:** `src/paycli/transactions.py` → `average_transaction()` (line 23)
- **Root cause (from RCA):** reachable empty input (`nargs="*"`) divides by `len([]) == 0`; no
  guard, no defined empty result.

**Before**
```python
def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount.

    BUG-B: divides by ``len`` with no guard for an empty sequence, so an empty
    input raises ``ZeroDivisionError`` instead of returning 0.
    """
    return sum(amounts) / len(amounts)
```

**After**
```python
def average_transaction(amounts: Sequence[float]) -> float:
    """Return the average transaction amount; 0.0 for an empty sequence."""
    if not amounts:
        return 0.0
    return sum(amounts) / len(amounts)
```

**Test command (proves the fix):**
```bash
python -m pytest tests/test_baseline.py::test_average_of_empty_is_zero \
                 tests/test_baseline.py::test_average_basic -q
```
Expected: 2 passed. `average_transaction([])` returns `0.0` (no `ZeroDivisionError`);
`average_transaction([10,20,30]) == 20.0` unchanged.

> After Changes 1 + 2 the entire baseline suite is GREEN — run
> `python -m pytest tests/test_baseline.py -q` (expected: 6 passed) as a milestone gate.

---

## Change 3 — VULN-1: remove `shell=True` command injection

- **File / symbol:** `src/paycli/report.py` → `export_report()` (line 21), plus import at line 9.
- **Root cause (from RCA):** untrusted `path` interpolated into a shell string run with
  `shell=True`; the shell is unnecessary for plain file I/O.
- **Contract to preserve:** `cli.py:38` does `return export_report(args.path)` and `main()` returns
  `int`, so `export_report` must keep returning an `int` (0 = success).

**Before** (imports, line 9)
```python
import subprocess
```
**Before** (function, line 21)
```python
def export_report(path: str) -> int:
    """Concatenate the file at ``path`` into ``report.txt``.

    VULN-1: builds a shell command from caller-supplied input with ``shell=True``,
    enabling command injection (e.g. ``path = "x; rm -rf ."``).
    """
    return subprocess.call(f"cat {path} > report.txt", shell=True)
```

**After** (imports — replace `subprocess` with `shutil`)
```python
import shutil
```
**After** (function)
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

Notes:
- `path` is now treated strictly as a filename. An injection payload such as `"x; rm -rf ."` is
  passed to `open()` as a literal (missing) filename → `OSError` → return `1`, **no command runs**.
- Return-type contract (`int`, 0 = success) preserved for `cli.py`.

**Test command (proves the fix):**
```bash
# 1) Static: no shell-injection finding (B602/B605) remains.
bandit -r src/paycli/report.py
# 2) Functional: injection payload is inert (returns 1, executes nothing) and a real copy works.
python -c "
from paycli.report import export_report
import os
assert export_report('x; rm -rf .') == 1          # payload treated as a filename, not a command
open('src_demo.txt','w').write('hello')
assert export_report('src_demo.txt') == 0          # legitimate copy succeeds
assert open('report.txt').read() == 'hello'
os.remove('src_demo.txt'); os.remove('report.txt')
print('VULN-1 OK')
"
```
Expected: bandit reports **no** B602/B605 (shell) issue for `report.py`; the script prints
`VULN-1 OK`. (A dedicated FIRST injection test is later added by the unit-test-generator.)

---

## Change 4 — VULN-2: move hardcoded secret to env var

- **File / symbol:** `src/paycli/report.py` → module-level `API_KEY` (line 12), plus `os` import.
- **Root cause (from RCA):** secret literal committed in source; no external config lookup.
- **Policy:** CLAUDE.md "No secrets in committed code" → remediate to an environment variable.

**Before** (line 11–12)
```python
# VULN-2: hardcoded secret committed in source (fake value, for the security agent to flag).
API_KEY = "sk-live-DEMO0000000000000000000000"
```

**After** (add `import os` with the other imports; replace the literal)
```python
import os
...
# API key is read from the environment, never committed to source.
API_KEY = os.environ.get("PAYCLI_API_KEY", "")
```

> Combined import block for `report.py` after Changes 3 + 4:
> ```python
> import os
> import shutil
> ```

**Test command (proves the fix):**
```bash
# 1) No hardcoded-secret finding (B105) and the literal is gone from source.
bandit -r src/paycli/report.py
grep -n "sk-live-DEMO" src/paycli/report.py || echo "secret literal absent"
# 2) Behaviour: API_KEY honours the environment.
PAYCLI_API_KEY=from-env python -c "
import importlib, paycli.report as r
importlib.reload(r)
assert r.API_KEY == 'from-env', r.API_KEY
print('VULN-2 OK')
"
```
Expected: bandit reports **no** B105 for `report.py`; `grep` prints `secret literal absent`; the
script prints `VULN-2 OK`.

---

## Full-suite / quality-gate verification (after all four changes)

```bash
ruff check src tests
mypy
bandit -r src/paycli                       # no HIGH severity
radon cc -nc src/paycli                    # no grade C-or-worse
python -m pytest --cov=paycli --cov-report=term-missing -q
```
Expected: ruff clean · mypy clean (strict) · bandit no HIGH · radon no C+ · baseline suite GREEN.
Coverage **≥ 90%** on `src/paycli/` is finalised by the unit-test-generator stage (it adds the
FIRST tests for the now-safe `export_report` paths and the VULN-1 injection-blocked case).

---

## Handoff -> bug-fixer

Apply the four changes **in the order above**, running the per-change test command immediately
after each edit and stopping to reflect/retry on any failure (per CLAUDE.md "Fail on test failure"):

1. **Change 1 — BUG-A** `src/paycli/transactions.py:32` — `<` → `<=`; run the limit tests.
2. **Change 2 — BUG-B** `src/paycli/transactions.py:23` — add `if not amounts: return 0.0` guard;
   run the average tests, then confirm the full baseline suite is GREEN (6 passed).
3. **Change 3 — VULN-1** `src/paycli/report.py` — swap `import subprocess` → `import shutil`;
   rewrite `export_report` to copy via file I/O (no shell); run bandit + the functional script.
4. **Change 4 — VULN-2** `src/paycli/report.py` — add `import os`; replace the literal with
   `os.environ.get("PAYCLI_API_KEY", "")`; run bandit + the env-var check.

Final: run the full quality gate (ruff · mypy · bandit · radon · pytest). Then hand the changed
files (`transactions.py`, `report.py`) to the **security-verifier** (report-only) and the
**unit-test-generator** (FIRST tests + coverage ≥ 90%).

Gate status: **open** — CHECKPOINT 2 is the human review of *this* plan before implementation.
