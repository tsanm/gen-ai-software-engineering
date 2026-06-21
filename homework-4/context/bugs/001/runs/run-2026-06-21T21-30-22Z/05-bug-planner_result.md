# Bug Planner — Implementation Plan (batch 001)

Mechanically-executable plan derived from `context/bugs/001/verified-rca.md`
(verdict: **VERIFIED WITH NOTES**, 4/4 root causes fundamental, 17/17 `file:line`s match,
side-effect surface **Low**). Each change below gives file · symbol · exact **before** · exact
**after** · **test command** · **rollback**. Plan only — no code edited.

All test commands run from the repo root
(`/Users/owner/src/gen-ai-software-engineering/homework-4`). `pyproject.toml` sets
`pythonpath = ["src"]`, so `python -m pytest …` resolves `paycli` without install.

Carried-forward note (**N1**, non-blocking): the boundary and empty-input tests already exist as
**RED baseline** tests (`tests/test_baseline.py:12-14`, `:25-27`). This plan **extends/relies on**
them — it does **not** add duplicates. The new VULN-1 injection-blocked test is the
unit-test-generator's job (`tests/test_baseline.py:5-6`), not this plan's.

---

## 1. Changes

### Change 1 — BUG-A: inclusive daily-limit boundary
- **File · symbol:** `src/paycli/transactions.py` · `is_within_daily_limit`
- **Root cause:** strict `<` excludes the endpoint; intended *inclusive* upper bound never modelled
  (verified-rca §2 BUG-A; fault at `transactions.py:32`).
- **Before** (`transactions.py:32`):
  ```python
      return spent + amount < limit
  ```
- **After** (`transactions.py:32`):
  ```python
      return spent + amount <= limit
  ```
- **Test command:**
  ```bash
  python -m pytest "tests/test_baseline.py::test_limit_exactly_at_limit_is_allowed" \
                   "tests/test_baseline.py::test_limit_over_is_rejected" \
                   "tests/test_baseline.py::test_limit_under_is_allowed" -q
  ```
  Expect: 3 passed. `test_limit_exactly_at_limit_is_allowed` flips RED→GREEN
  (`60+40 == 100 == limit` → True); the `over` (101→False) and `under` (99→True) cases stay green
  (no endpoint change) — confirms no side effect (verified-rca §4).
- **Rollback:** restore `<` on `transactions.py:32` (revert this one line).

### Change 2 — BUG-B: guard empty-sequence average
- **File · symbol:** `src/paycli/transactions.py` · `average_transaction`
- **Root cause:** implicit `len ≥ 1` precondition never reconciled with the public `nargs="*"`
  contract that admits `[]`; docstring already specifies "return 0" (verified-rca §2 BUG-B;
  intent at `transactions.py:20-21`, fault at `:23`).
- **Before** (`transactions.py:23`):
  ```python
      return sum(amounts) / len(amounts)
  ```
- **After** (`transactions.py:23`):
  ```python
      if not amounts:
          return 0.0
      return sum(amounts) / len(amounts)
  ```
  Return type stays `float` (`0.0`), satisfying the `-> float` signature under `mypy --strict`.
- **Test command:**
  ```bash
  python -m pytest "tests/test_baseline.py::test_average_of_empty_is_zero" \
                   "tests/test_baseline.py::test_average_basic" -q
  ```
  Expect: 2 passed. `test_average_of_empty_is_zero` flips RED→GREEN (`[]` → `0.0`, no raise;
  `0.0 == 0` is True); `test_average_basic` (`[10,20,30]→20.0`) stays green — non-empty path
  unchanged (verified-rca §4).
- **Rollback:** delete the two guard lines, leaving only
  `return sum(amounts) / len(amounts)` on `transactions.py:23`.

### Change 3 — VULN-2: read credential from the environment
- **File · symbol:** `src/paycli/report.py` · module-level `API_KEY` (and add `import os`)
- **Root cause:** credential lifecycle bound to code; no secret-injection seam (verified-rca §2
  VULN-2; fault at `report.py:12`). Grep confirms **zero readers** of `API_KEY` (verified-rca §4),
  so import-time behaviour is the only regression surface and a default-empty value is safe.
- **Before** (`report.py:7-12`):
  ```python
  from __future__ import annotations

  import subprocess

  # VULN-2: hardcoded secret committed in source (fake value, for the security agent to flag).
  API_KEY = "sk-live-DEMO0000000000000000000000"
  ```
- **After** (`report.py:7-12`):
  ```python
  from __future__ import annotations

  import os
  import shutil

  # Credential is injected from the environment; no secret is committed in source.
  API_KEY = os.environ.get("PAYCLI_API_KEY", "")
  ```
  (`import subprocess` is removed and `import shutil` added here because Change 4 — same file —
  drops the only `subprocess` use and introduces `shutil`. Applying both imports in one edit keeps
  `report.py` ruff-clean — no `F401` unused-import — at every intermediate state.)
- **Test command:**
  ```bash
  bandit -r src/paycli/report.py -q          # expect: no HIGH (hardcoded-secret B105 gone)
  python -c "import paycli.report as r; print('import ok; API_KEY empty=' + str(r.API_KEY == ''))"
  grep -n "sk-live-DEMO" src/paycli/report.py; test $? -ne 0 && echo "literal removed"
  ```
  Expect: bandit reports no HIGH; module imports without error and `API_KEY` defaults to `""` when
  `PAYCLI_API_KEY` is unset; the literal no longer appears in source.
- **Rollback:** restore the original `import subprocess` line and the hardcoded
  `API_KEY = "sk-live-DEMO0000000000000000000000"`; remove `import os`/`import shutil`.
  (If Change 4 is also being rolled back, revert both together since they share the import block.)

### Change 4 — VULN-1: remove `shell=True`; no-shell file copy
- **File · symbol:** `src/paycli/report.py` · `export_report`
- **Root cause:** design choice to invoke a shell for a file op while treating `path` as trusted —
  erased code/data boundary (verified-rca §2 VULN-1, **Critical**; fault at `report.py:21`).
  Constraint (verified-rca §4): the `int` status contract consumed at `cli.py:38` must be preserved
  and `report.txt` must still be produced; there is no existing test for `export_report`.
- **Before** (`report.py:15-21`):
  ```python
  def export_report(path: str) -> int:
      """Concatenate the file at ``path`` into ``report.txt``.

      VULN-1: builds a shell command from caller-supplied input with ``shell=True``,
      enabling command injection (e.g. ``path = "x; rm -rf ."``).
      """
      return subprocess.call(f"cat {path} > report.txt", shell=True)
  ```
- **After** (`report.py:15-22`):
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
  No shell, no subprocess: `path` can never be parsed as a command. `int` contract preserved
  (0 success / 1 failure), `report.txt` still produced. `import shutil` is added by Change 3's edit.
- **Test command:**
  ```bash
  bandit -r src/paycli/report.py -q          # expect: no HIGH (B602 subprocess+shell=True gone)
  # functional: a benign source copies and returns 0
  printf 'hello\n' > /tmp/paycli_src.txt
  python -m paycli export /tmp/paycli_src.txt; echo "exit=$?"   # expect exit=0; report.txt == source
  # injection string is treated as a literal (missing) path, not executed
  python -m paycli export 'x; touch /tmp/paycli_pwned'; echo "exit=$?"   # expect exit=1
  test ! -e /tmp/paycli_pwned && echo "injection blocked (no side effect)"
  python -m pytest -q          # full baseline still green (no regression at cli.py:38)
  ```
  Expect: bandit no HIGH; benign export returns 0 and writes `report.txt`; the injection string
  yields exit 1 and creates **no** `/tmp/paycli_pwned`; full suite green.
- **Rollback:** restore the original docstring and
  `return subprocess.call(f"cat {path} > report.txt", shell=True)`, and (with Change 3) restore
  `import subprocess` / drop `import shutil`.

---

## 2. Order & dependencies

Safest first; each change is independently revertable.

1. **Change 1 (BUG-A)** — one-operator edit, locked by an existing RED test. Lowest risk.
2. **Change 2 (BUG-B)** — small guard, locked by an existing RED test.
3. **Change 3 (VULN-2)** — import block + `API_KEY`; zero readers, import-time-only surface.
4. **Change 4 (VULN-1)** — function-body rewrite; highest behavioural change.

**Dependency:** Changes 3 and 4 edit the **same file** (`report.py`) and share its import block.
Change 3's edit establishes the final imports (`os`, `shutil`; drops `subprocess`) that Change 4's
body relies on. **Apply Change 3 before Change 4**, and run Change 4's test only after both are in
place (between the two edits `report.py` may transiently reference `shutil` before import — do not
run tests in that window). Changes 1 and 2 are fully independent of each other and of report.py.

---

## 3. Success criteria

The fix is complete when **all** hold:

- `python -m pytest -q` → all of `tests/test_baseline.py` green, specifically the two formerly-RED
  tests now pass: `test_limit_exactly_at_limit_is_allowed`, `test_average_of_empty_is_zero`.
- `bandit -r src/paycli -q` → **no HIGH** findings (B602 shell-injection and B105 hardcoded-secret
  both cleared).
- `grep -rn "sk-live-DEMO" src/` → no match (secret literal gone from source).
- `python -m paycli export <benign file>` returns 0 and writes `report.txt`; an injection-style
  `path` returns 1 and executes nothing.
- `ruff check src/paycli` and `mypy src/paycli` clean (no unused `subprocess` import; `average`
  still returns `float`).

These feed the project quality gate (CLAUDE.md): `ruff` · `mypy` · `bandit` (no HIGH) · `radon`
(no C-or-worse) · `pytest` coverage ≥ 90% on `src/paycli/`.

## 4. References — root causes addressed

- **BUG-A** — `src/paycli/transactions.py:32` (verified-rca §2/§4; research §BUG-A).
- **BUG-B** — `src/paycli/transactions.py:23` (verified-rca §2/§4; research §BUG-B).
- **VULN-2** — `src/paycli/report.py:12` (verified-rca §2/§4 — zero readers; research §VULN-2).
- **VULN-1** — `src/paycli/report.py:21` (verified-rca §2/§4 — preserve `int` for `cli.py:38`;
  research §VULN-1).

---

## Handoff → bug-fixer

CHECKPOINT 2 plan is ready and self-contained. Execute Changes 1→4 **in the listed order**, running
each change's test command immediately after applying it; for `report.py`, apply Change 3 then
Change 4 and run Change 4's tests only once both are in place. Stop and reflect if any test fails,
then retry before continuing (CLAUDE.md "fail on test failure").

- Every change has exact before/after, a test command, and a rollback.
- Each change traces to a verified, fundamental root cause (verified-rca §2).
- **No new tests in this stage** — the empty/boundary tests already exist (RED baseline, N1); the
  VULN-1 injection-blocked test is the unit-test-generator's job (`tests/test_baseline.py:5-6`).
- No open questions.
