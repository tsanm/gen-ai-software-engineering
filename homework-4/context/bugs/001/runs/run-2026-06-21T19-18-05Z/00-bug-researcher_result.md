# Bug Researcher Result — paycli (batch 001)

Architect mode (read-only). Documents what **exists** in `src/` for each seeded
issue in `context/bugs/001/bug-context.md`, with exact `file:line` evidence and a
verbatim snippet at each location. No code was edited.

## Findings

| Issue | Claim (defect that exists) | `file:line` | Verbatim snippet |
|-------|----------------------------|-------------|------------------|
| BUG-A | Daily-limit check uses strict `<`, so a spend landing exactly on the limit is wrongly rejected (boundary off-by-one). | `src/paycli/transactions.py:32` | `    return spent + amount < limit` |
| BUG-B | `average_transaction` divides by `len(amounts)` with no empty guard → `ZeroDivisionError` on empty input. | `src/paycli/transactions.py:23` | `    return sum(amounts) / len(amounts)` |
| VULN-1 | `export_report` builds a shell command from caller-supplied `path` with `shell=True` → command injection (bandit B602). | `src/paycli/report.py:21` | `    return subprocess.call(f"cat {path} > report.txt", shell=True)` |
| VULN-2 | Hardcoded API-key secret literal committed in source. | `src/paycli/report.py:12` | `API_KEY = "sk-live-DEMO0000000000000000000000"` |

### Supporting context
- **BUG-A** is reached from the CLI at `src/paycli/cli.py:36`
  (`print(transactions.is_within_daily_limit(args.spent, args.amount, args.limit))`).
  Repro math: `check-limit 60 40 100` → `60 + 40 = 100`; `100 < 100` is `False`
  (should be `True`). Fix per context: `<` → `<=`.
- **BUG-B** is reached from the CLI at `src/paycli/cli.py:34`
  (`print(transactions.average_transaction(args.amounts))`); `average` with no
  amounts yields `len([]) == 0`. Expected fix: return `0` on empty.
- **VULN-1** import of `subprocess` at `src/paycli/report.py:9`; the unsanitized
  `path` flows from CLI `export` parser at `src/paycli/cli.py:27` → `cli.py:38`
  (`return export_report(args.path)`). Expected fix: no shell; argv list /
  validated path.
- **VULN-2** secret is module-level and would be importable/visible to anyone
  reading source. Expected fix: read from environment, no literal in source.

## Notes
- All four locations carry explicit author seed-comments naming the defect
  (`transactions.py:20-22`, `:29-31`; `report.py:11`, `:18-20`), which corroborate
  but are independent of the located code lines above.
- No ambiguity: each context-listed symbol resolves to exactly one definition in
  `src/`. No duplicate or shadowed definitions found.
- `total()` (`transactions.py:12-14`) is not a seeded defect and was not flagged.

## Handoff -> research-verifier
Verify each of the following `file:line` claims against source:

1. `src/paycli/transactions.py:32` — `is_within_daily_limit` uses `<` (BUG-A).
2. `src/paycli/transactions.py:23` — `average_transaction` divides by `len` with no empty guard (BUG-B).
3. `src/paycli/report.py:21` — `export_report` uses `subprocess.call(..., shell=True)` on user `path` (VULN-1).
4. `src/paycli/report.py:12` — hardcoded `API_KEY` secret literal (VULN-2).

Cross-reference call sites: `cli.py:34` (average), `cli.py:36` (check-limit),
`cli.py:38` + `cli.py:27` (export path), and `report.py:9` (`import subprocess`).
