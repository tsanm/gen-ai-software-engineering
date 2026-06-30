# RCA Analyst — Decision Log (batch 001)

| step | decision | reason | evidence |
|------|----------|--------|----------|
| Read verified research | Proceed with RCA | Quality level **Verified**, PASS, zero discrepancies — safe to analyze | verified-research.md §1,§4 |
| Re-open source | Confirm each fault line before reasoning | RCA must ground every why in real `file:line`, not narration | transactions.py:23,32; report.py:12,21; cli.py:19,27,34,36,38 |
| BUG-A root cause | Fundamental cause = unspecified inclusive boundary (`<` vs `<=`), not "wrong operator" | Operator is the symptom; the *why* is that "is the limit allowed?" was never specified/tested | transactions.py:27,29-30,32 |
| BUG-A depth | 5 Whys (5 steps) | Boundary/spec defect is subtle; drive past operator to missing boundary test | transactions.py:26-32 |
| BUG-B root cause | Fundamental cause = precondition/contract gap (body assumes `len≥1`; CLI admits `[]`) | "len is 0" is symptom; real why is domain mismatch between caller grammar and body | transactions.py:23 × cli.py:19 |
| BUG-B depth | 5 Whys | Edge-case + contract mismatch warrants full chain to the untested empty domain | transactions.py:17-23, cli.py:34 |
| VULN-1 severity | Critical | Arbitrary command execution via attacker-controlled `path` | report.py:21, cli.py:27/38 |
| VULN-1 root cause | Fundamental cause = code/data boundary erased; shell invoked for a file op, path treated as trusted | `shell=True` f-string is symptom; design never separated command from untrusted argument | report.py:15,21; cli.py:27 |
| VULN-2 root cause | Fundamental cause = secret bound to source; no config/env seam | Literal is symptom; why = secret lifecycle tied to code, no injection point | report.py:9,12 |
| VULN-2 regression scope | Note import-time only | No verified call path reads `API_KEY`, so risk is limited to module load | report.py:12; verified-research.md §2 |
| Scope discipline | No fixes, no code edits | rca-analyst is read-only/analysis-only per role contract | (role) |
| Risks section | List per-issue regression + cross-cutting independence | Hand the planner the boundary/contract decisions needed before implementing | transactions.py:14,32; report.py:12,21; cli.py:38 |
| Handoff target | rca-verifier | Quality gate before CHECKPOINT 1 / planning | role handoff |
