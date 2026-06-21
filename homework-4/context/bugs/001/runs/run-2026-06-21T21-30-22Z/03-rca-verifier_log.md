# RCA Verifier — Decision Log (batch 001)

| step | decision | reason | evidence |
|------|----------|--------|----------|
| Read RCA + grounding | Reviewed `rca.md` and its source `verified-research.md` | Verify against what RCA claims to be grounded in | `rca.md:1-201`; `verified-research.md:1-71` |
| Verify code file:line | All 17 cited code locations exist and match verbatim | Trust-by-reading, not by claim | `transactions.py:14,17-23,23,26-32,32`; `report.py:9,12,15,21`; `cli.py:19,27,34,36,38` |
| BUG-A depth | PASS — fundamental (unmodelled inclusive boundary) reached at Why-3/4 | `<` is symptom; chain deepens to spec gap "is limit allowed?" | `rca.md:38-47`; `transactions.py:29-32` |
| BUG-B depth | PASS — fundamental (precondition/contract gap) reached at Why-4 | body assumes `len≥1`; `nargs="*"` admits `[]` | `rca.md:68-78`; `transactions.py:23` × `cli.py:19` |
| VULN-1 depth | PASS — fundamental (erased code/data boundary) at Why-5; Critical confirmed | shell parses untrusted `path`; no command/arg separation | `rca.md:99-109`; `report.py:21` ← `cli.py:27` |
| VULN-2 depth | PASS — fundamental (no config seam; lifecycle bound to code) at Why-4 | secret is source literal, no `os.environ` read | `rca.md:129-138`; `report.py:9,12` |
| Side-effect scan | Low overall; `API_KEY` has zero readers (confirmed) | grep all affected symbols across repo | `is_within_daily_limit`→`cli.py:36`,`test_baseline.py:14,18,22`; `average_transaction`→`cli.py:34`,`test_baseline.py:27,31`; `export_report`→`cli.py:38`; `API_KEY`→only `report.py:12` |
| **N1 — factual error** | RCA's "(absence) of tests" at BUG-A/BUG-B Why-5 is **false** | RED baseline tests already cover both cases | `test_baseline.py:12-14` (exact-limit), `:25-27` (empty input) |
| Severity of N1 | Note, not blocker | fundamental cause reached before Why-5; fix direction unchanged; existing RED test strengthens RCA | `rca.md:42,72` vs `test_baseline.py:1-7,12-27` |
| N2 — VULN-2 Why-5 | Minor, no correction | "no blocking signal in code" true at commit; `bandit` gate exists in CI quality gate | `rca.md:133`; `CLAUDE.md` quality gate |
| Verdict | **VERIFIED WITH NOTES** → CHECKPOINT 1 → bug-planner | causes fundamental, all file:line verified, risk Low; only narrative correction outstanding | this log + `03-rca-verifier_result.md` |
| Anti-duplication flag | Carry N1 forward: do not re-create boundary/empty tests | they exist as RED baseline; extend, don't duplicate | `test_baseline.py:5-6` |
