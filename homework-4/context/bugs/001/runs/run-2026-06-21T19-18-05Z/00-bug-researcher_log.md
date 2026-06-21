# Bug Researcher — Decision Log

| step | decision | reason | evidence |
|------|----------|--------|----------|
| 1 | Read `bug-context.md` | Establish the seeded-issue inventory (BUG-A/B, VULN-1/2) | `context/bugs/001/bug-context.md:11-23` |
| 2 | Open all 3 source files (`transactions.py`, `report.py`, `cli.py`) | Context names these as the only source files; locate each defect at source | `bug-context.md:9` |
| 3 | Locate BUG-A | Found strict `<` in daily-limit check | `transactions.py:32` |
| 4 | Locate BUG-B | Found `sum/len` with no empty guard | `transactions.py:23` |
| 5 | Locate VULN-1 | Found `subprocess.call(f"cat {path}...", shell=True)` on user input | `report.py:21` (import at `report.py:9`) |
| 6 | Locate VULN-2 | Found hardcoded `API_KEY` literal at module scope | `report.py:12` |
| 7 | Trace CLI call sites | Confirm each defect is reachable from user input | `cli.py:34,36,38`; export path arg `cli.py:27` |
| 8 | Verify BUG-A repro math | `60+40=100`, `100<100=False` matches context's expected `False` | `bug-context.md:14` vs `transactions.py:32` |
| 9 | Check for ambiguity / duplicates | Each symbol resolves to exactly one definition; no shadowing | single defs in `transactions.py`, `report.py` |
| 10 | Write result + handoff | Pass 4 `file:line` claims to research-verifier | `00-bug-researcher_result.md` |
