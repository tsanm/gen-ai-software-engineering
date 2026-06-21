# RCA Analyst Decision Log — paycli (batch 001)

| step | decision | reason | evidence |
|------|----------|--------|----------|
| 1 | Read `verified-research.md` as authoritative input | Research Quality is **Verified**; gate open for RCA | `verified-research.md:11,64-65` |
| 2 | Re-read source at each cited line before analysis | Ground every Why in current source, not just the research summary | `transactions.py:23,32`; `report.py:12,21`; `cli.py:34,36,38` |
| 3 | Scope to the 4 Verified defects only | Single responsibility; analyze confirmed issues, not new hunts | `verified-research.md:68-78` |
| 4 | BUG-A root cause = inclusive rule coded with exclusive `<`, no boundary test | Docstring says "within limit" (inclusive) but operator is `<`; equality rejected | `transactions.py:27,29-30,32` |
| 5 | BUG-B root cause = unhandled empty-sequence edge case, no guard | `len([])==0` divides by zero; empty input reachable via CLI `nargs="*"` | `transactions.py:23`; `cli.py:19,34` |
| 6 | VULN-1 root cause = untrusted input into `shell=True` cmd + needless shell | `path` from CLI arg interpolated unsanitized; shell unnecessary for file copy | `report.py:21`; `cli.py:27,38`; `report.py:9` |
| 7 | VULN-2 root cause = secret in source, no config/env boundary | Literal credential at module scope; no `os.environ`/config lookup exists | `report.py:12` |
| 8 | Output root cause only; propose no fixes | Golden rule: RCA is read-only; fixes belong to the planner | `CLAUDE.md` golden rules |
| 9 | Wrote result + handoff to rca-verifier | Immutable per-run artifact ending in `## Handoff` | this run folder |
