# Bug Context — paycli (batch 001)

Author-written seed for the 4-agent pipeline. Describes the app, the intentional
defects, and how to reproduce each. The pipeline reads this as its starting input.

## App under test
`paycli` — a tiny payments/transactions CLI (`python -m paycli <command>`):
- `total <amounts…>` · `average <amounts…>` · `check-limit <spent> <amount> <limit>` · `export <path>`
- Source: `src/paycli/transactions.py`, `src/paycli/report.py`, `src/paycli/cli.py`.

## Seeded issues
| ID | Type | Location | Defect | Reproduction (pre-fix) |
|----|------|----------|--------|------------------------|
| BUG-A | Logic / boundary | `transactions.is_within_daily_limit` | uses strict `<`; a spend exactly at the limit is wrongly rejected | `python -m paycli check-limit 60 40 100` → prints `False` (should be `True`); `pytest -k limit_exactly` fails |
| BUG-B | Edge case | `transactions.average_transaction` | divides by `len` with no empty guard | `python -m paycli average` → `ZeroDivisionError`; `pytest -k average_of_empty` fails |
| VULN-1 | Command injection (HIGH) | `report.export_report` | `subprocess.call(f"cat {path} …", shell=True)` on user input | `python -m paycli export "x; touch pwned.txt"` creates `pwned.txt`; `bandit -r src` flags B602 |
| VULN-2 | Hardcoded secret (MEDIUM) | `report.API_KEY` | secret literal committed in source | visible in `src/paycli/report.py` |

## Expected after the pipeline
- BUG-A → `<=`; BUG-B → returns `0` on empty.
- VULN-1 → no shell; argv list / validated path; injection cannot execute.
- VULN-2 → secret read from environment; no literal in source.
- Baseline suite GREEN; new FIRST tests added for the changed code (incl. injection-blocked).
