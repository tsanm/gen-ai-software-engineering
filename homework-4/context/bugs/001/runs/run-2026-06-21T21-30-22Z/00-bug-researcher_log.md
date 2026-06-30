# Bug Researcher — Decision Log (batch 001)

| step | decision | reason | evidence |
|------|----------|--------|----------|
| Read context | Parsed `bug-context.md`; enumerated 4 seeded issues (BUG-A, BUG-B, VULN-1, VULN-2) | First pipeline stage must work from author seed | `context/bugs/001/bug-context.md:11-17` |
| Locate BUG-A | Documented strict `<` boundary behaviour at executable line, not the comment | Claim must cite the line that runs | `src/paycli/transactions.py:32` |
| Locate BUG-B | Documented unguarded `len` division | Empty input reaches division via `nargs="*"` | `src/paycli/transactions.py:23`, `src/paycli/cli.py:19` |
| Locate VULN-1 | Documented f-string + `shell=True` on user `path` | User input flows unvalidated from CLI to shell | `src/paycli/report.py:21`, `src/paycli/cli.py:27,38` |
| Locate VULN-2 | Documented hardcoded `API_KEY` literal | Secret committed in source | `src/paycli/report.py:12` |
| Verify call paths | Opened `cli.py` to confirm each defect is reachable from a subcommand | Downstream RCA/fix needs reachability facts | `src/paycli/cli.py:34,36,38` |
| Scope check | Recorded `total` as non-issue; no edits made; no evaluative language | Researcher describes behaviour only | `src/paycli/transactions.py:14` |
| Write artifacts | Emitted result + this log; ended result with `## Handoff → research-verifier` | Structured immutable handoff per pipeline contract | run folder `run-2026-06-21T21-30-22Z/` |
