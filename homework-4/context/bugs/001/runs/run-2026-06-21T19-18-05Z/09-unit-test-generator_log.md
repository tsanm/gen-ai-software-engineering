# Unit-Test-Generator Decision Log

| step | decision | reason | evidence |
|------|----------|--------|----------|
| Read fix-summary.md | Used as primary spec for what changed | Authoritative per-change record produced by bug-fixer | 4 changes listed: BUG-A (`<=`), BUG-B (empty guard), VULN-1 (no `shell=True`), VULN-2 (env var) |
| Read transactions.py + report.py | Confirmed current post-fix state of changed files | Verify source matches fix-summary before writing tests | `is_within_daily_limit` uses `<=`; `average_transaction` has `if not amounts` guard; `export_report` uses file I/O, no subprocess |
| Read test_baseline.py | Identified existing coverage to avoid duplication | Agent mandate: do not duplicate baseline tests | Baseline covers: `(60,40,100)→True`, `(60,41,100)→False`, `(60,39,100)→True`, `[]→0`, `[10,20,30]→20.0`, total |
| Scoped BUG-A tests | Added 6 boundary probes from different angles (zero-base, float precision, large values, type check) | Baseline uses `60+X` pattern; complementary tests at `0+100`, `99.99+0.01`, `9000+1000` expand signal | No overlap with baseline cases |
| Scoped BUG-B tests | Added 4 tests: explicit no-raise, float type check, single-element, negative values | Baseline checks `[] == 0` but not `isinstance(result, float)` or exception contract explicitly | `test_empty_does_not_raise` uses `pytest.fail` pattern for unambiguous contract |
| Scoped VULN-1 tests | Added 4 tests including injection-payload side-effect assertion | Core requirement: injection payload must not execute; use `tmp_path` as specified | `tmp_path / "injected.txt"` not created when `export_report` called with `;touch ...` payload |
| Used monkeypatch.chdir in copy test | Isolate `report.txt` write (CWD-relative) to tmp_path | Without chdir, `report.txt` would land in project root — not isolated/repeatable | `export_report` opens `"report.txt"` without a path prefix |
| Added source-inspection test | Assert `shell=True` and `subprocess` absent from `export_report` source | Belt-and-suspenders: code-level proof independent of behavioral test | `inspect.getsource(report.export_report)` checked |
| Ran pytest --cov=paycli | All 20 tests pass; changed files at 100% coverage | Quality gate requires test suite green and coverage verified | `transactions.py` 100%, `report.py` 100%; 0 failures |
| Noted 43% overall vs 100% on changed files | cli.py / __main__.py excluded from scope | Unit-test-generator mandate is changed code only; CLI tests are outside scope | Unchanged files have 0% coverage; that is expected and pre-existing |
