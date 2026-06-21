# Research Verifier — Decision Log

| step | decision | reason | evidence |
|------|----------|--------|----------|
| Load skill | Applied research-quality-measurement levels & required sections | Contract requires a consistent Research Quality label | `.claude/skills/research-quality-measurement.md:11-26` |
| Read input | Parsed 4 core claims + 5 supporting cross-refs | Need every cited `file:line` to verify | `codebase-research.md:9-48` |
| Verify BUG-A | Snippet matches | Source line equals quoted snippet | `transactions.py:32` = `return spent + amount < limit` |
| Verify BUG-B | Snippet matches | Source line equals quoted snippet | `transactions.py:23` = `return sum(amounts) / len(amounts)` |
| Verify VULN-1 | Snippet matches | Source line equals quoted snippet | `report.py:21` = `subprocess.call(f"cat {path} > report.txt", shell=True)` |
| Verify VULN-2 | Snippet matches | Source line equals quoted snippet | `report.py:12` = `API_KEY = "sk-live-DEMO0000000000000000000000"` |
| Verify cross-refs | All 5 resolve | Call sites / import / arg confirm data flow | `cli.py:34`, `cli.py:36`, `cli.py:27`, `cli.py:38`, `report.py:9` |
| Check seed comments | Present within cited ranges | Corroborate located defects | `report.py:11,18-19`; `transactions.py:20-21,29-30` |
| Check non-defect | `total()` correctly not flagged | Avoid false positives | `transactions.py:12-14` |
| Abbreviated `print(...)` snippets | Not a discrepancy | Quotes the call expr, not full line; no claim affected | `codebase-research.md:17,21` vs `cli.py:34,36` |
| Assign level | **Verified** | 100% of claims resolve with exact snippet match; no discrepancies | Gate open → handoff to rca-analyst |
