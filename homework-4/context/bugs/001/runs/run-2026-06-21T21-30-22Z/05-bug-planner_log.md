# Bug Planner — Decision Log (batch 001)

| step | decision | reason | evidence |
|------|----------|--------|----------|
| Inputs | Planned only from `verified-rca.md` + `verified-research.md`, then opened source to capture exact before-snippets | Plan must be mechanically executable; before/after must match source verbatim | verified-rca §3 (17/17 match); read `transactions.py`, `report.py`, `cli.py`, `test_baseline.py`, `pyproject.toml` |
| BUG-A | Change `<` → `<=` on `transactions.py:32` (one operator) | Inclusive upper bound never modelled; minimal fix locked by existing RED test | verified-rca §2/§4 BUG-A; `test_baseline.py:12-14` |
| BUG-B | Add `if not amounts: return 0.0` guard before division at `transactions.py:23` | Empty input allowed by `nargs="*"`; docstring specifies return 0; `0.0` keeps `-> float` under mypy strict | verified-rca §2/§4 BUG-B; `transactions.py:20-21`; `test_baseline.py:25-27` |
| VULN-1 | Replace `subprocess.call(..., shell=True)` with `shutil.copyfile` in try/except, return 0/1 | Removes shell, treats `path` as pure data; preserves `int` contract + `report.txt` output | verified-rca §2/§4 VULN-1 (preserve int for `cli.py:38`); `report.py:21` |
| VULN-2 | `API_KEY = os.environ.get("PAYCLI_API_KEY", "")` | Inject secret from env; zero readers → default-empty is safe, no import-time crash; remediates committed secret | verified-rca §4 (zero readers); CLAUDE.md golden rule; `report.py:12` |
| Imports | Fold `import os` + `import shutil` add and `import subprocess` removal into one edit (Change 3) | Keeps `report.py` ruff-clean (no F401) at every intermediate state since Change 4 drops the only subprocess use | `report.py:9`; pyproject `[tool.ruff]` |
| Order | BUG-A → BUG-B → VULN-2 → VULN-1; apply VULN-2 before VULN-1 (same file) | Safest-first; Changes 3/4 share `report.py` import block, so import edit must precede body rewrite | verified-rca §4 (Low, independent); shared-file import dependency |
| Tests | Reuse existing RED baseline tests for BUG-A/BUG-B; add no tests; VULN tests via pytest+bandit+functional CLI checks | N1: boundary/empty tests already exist; injection test is unit-test-generator's job | verified-rca §1 N1, Handoff; `test_baseline.py:5-6` |
| Test cmd form | `python -m pytest …` / `python -m paycli …` from repo root | `pyproject.toml` sets `pythonpath=["src"]`; no install needed | `pyproject.toml:11-13` |
| Scope | No code modified; no open questions left | Planner is read-only; fixer must execute without guessing | CLAUDE.md golden rules; agent contract |
