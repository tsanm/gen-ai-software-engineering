# Bug Planner Decision Log — paycli (batch 001)

| step | decision | reason | evidence |
|------|----------|--------|----------|
| 1 | Read `verified-rca.md` as the only source of truth for which fixes to plan | Plan must derive from validated root causes, not re-investigate | `verified-rca.md` "Overall verdict — PASS (4/4)" + `## Handoff -> bug-planner` |
| 2 | Re-read live source for exact before-snippets | Snippets must match current file content byte-for-byte for the editor | `transactions.py:23,32`; `report.py:9,12,21`; `cli.py:38` |
| 3 | BUG-A: change `<` → `<=` only | Minimal lever named by RCA; inclusive "within limit" contract | `transactions.py:32` + contract `:27`; seed note `:29-30` |
| 4 | BUG-B: `if not amounts: return 0.0` guard before divide | Defines empty result + prevents ZeroDivisionError on reachable `[]` | `transactions.py:23`; reachability `cli.py:19,34`; baseline `test_average_of_empty_is_zero` |
| 5 | VULN-1: drop `shell=True`, use `shutil.copyfileobj` file I/O | Removes shell entirely (RCA "shell unneeded"); kills injection vector | `report.py:21`; RCA VULN-1 root cause |
| 6 | Keep `export_report` returning `int` (0 ok / 1 fail) | `cli.py:38` returns its value as the process exit code; contract must hold | `cli.py:38` `return export_report(args.path)`; `main() -> int` |
| 7 | VULN-2: `os.environ.get("PAYCLI_API_KEY", "")`, remove literal | CLAUDE.md "No secrets in committed code" → remediate to env var | `report.py:12`; CLAUDE.md golden rule |
| 8 | Order changes by file: transactions.py (1,2) then report.py (3,4) | Group edits per file; get baseline GREEN before security hardening | baseline pins only BUG-A/BUG-B; vulns verified by bandit |
| 9 | Per-change test cmds: pytest for BUG-A/B, bandit + functional for VULN-1/2 | Each change must have an independent proof; vulns lack baseline tests pre-generation | `tests/test_baseline.py`; `pyproject.toml` bandit/pytest config |
| 10 | Defer coverage ≥90% + FIRST injection test to unit-test-generator | Single-responsibility: planner specifies, test stage adds tests | CLAUDE.md agent roles; `test_baseline.py` docstring |
