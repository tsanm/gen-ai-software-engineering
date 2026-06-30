# Unit Test Generator — Decision Log (batch 001)

| step | decision | reason | evidence |
|---|---|---|---|
| Read fix-summary.md | Identified 4 changes: BUG-A (`<=`), BUG-B (empty guard), VULN-2 (env var), VULN-1 (`shutil.copyfile`) | Need to know exactly what changed before writing tests | `context/bugs/001/fix-summary.md` |
| Read test_baseline.py | Catalogued existing assertions: `is_within_daily_limit(60,40,100)`, `(60,41,100)`, `(60,39,100)`, `average_transaction([])`, `average_transaction([10,20,30])` | Must not duplicate baseline tests | `tests/test_baseline.py` |
| Read test_cli.py | Noted CLI-level coverage of export (benign path) and average-empty via CLI | Avoid duplicating CLI tests; target unit-level gaps | `tests/test_cli.py` |
| Read transactions.py | Confirmed `<=` fix at line 34 and empty guard at lines 23-25 | Need exact function signatures for test calls | `src/paycli/transactions.py` |
| Read report.py | Confirmed `shutil.copyfile` at line 24, `OSError` catch returns 1 | Needed to know expected return codes for injection test | `src/paycli/report.py` |
| BUG-A inputs chosen | Used `(0.0, 50.0, 50.0)` for at-limit and `(0.0, 50.01, 50.0)` for over-limit | Baseline used (60,40,100) family; new inputs provide independent coverage | Non-overlapping with baseline |
| BUG-B test split | Two tests: one checks return type is `float`, one uses try/except guard | Baseline only does `== 0`; float type and no-exception are distinct locked behaviours | Baseline line 27 uses `== 0` only |
| VULN-1 injection target | Side-effect file placed in `tmp_path / "pwned"`; payload `f"x; touch {pwned_file}"` | `tmp_path` is isolated per test run; side effect would be visible if injection executed | pytest `tmp_path` fixture docs |
| VULN-1 two asserts | Assert return code == 1 AND pwned file does not exist | Return code alone does not prove injection was blocked; file absence is the real proof | Fix summary: "injection string treated as literal missing path" |
| VULN-1 happy-path added | `test_vuln1_benign_path_succeeds` tests that `shutil.copyfile` still works for a real file | Fix must not break the benign case; `test_cli.py` covers CLI but not the unit function directly | `src/paycli/report.py` line 17 docstring |
| pytest run (generated only) | 6 passed; report.py 100%, transactions.py 80% (cli.py not exercised by generated tests) | Confirms generated tests are green in isolation | pytest output |
| pytest run (full suite) | 18 passed; 100% total coverage | No regressions; quality gate met | pytest --cov output |
