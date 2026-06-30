# Bug Researcher — Codebase Research (batch 001)

Factual documentation of each seeded issue from `context/bugs/001/bug-context.md`,
located in `src/` with exact `file:line` evidence and verbatim snippets. Facts only —
no critique, no fixes.

## 1. Findings

| Issue | Factual claim (observable behaviour) | `file:line` | Verbatim snippet |
|-------|--------------------------------------|-------------|------------------|
| BUG-A | `is_within_daily_limit` compares `spent + amount` against `limit` using strict `<`, so when the sum equals `limit` the function returns `False`. For inputs `(60, 40, 100)` the sum is `100`; `100 < 100` evaluates to `False`. | `src/paycli/transactions.py:32` | `return spent + amount < limit` |
| BUG-B | `average_transaction` divides `sum(amounts)` by `len(amounts)` with no guard for an empty sequence; for an empty input `len(amounts)` is `0` and the division raises `ZeroDivisionError`. | `src/paycli/transactions.py:23` | `return sum(amounts) / len(amounts)` |
| VULN-1 | `export_report` builds a shell command string from the caller-supplied `path` via an f-string and runs it with `subprocess.call(..., shell=True)`. The `path` value is interpolated unquoted into `cat {path} > report.txt`. | `src/paycli/report.py:21` | `return subprocess.call(f"cat {path} > report.txt", shell=True)` |
| VULN-2 | A secret literal is assigned to the module-level constant `API_KEY` in source. | `src/paycli/report.py:12` | `API_KEY = "sk-live-DEMO0000000000000000000000"` |

### Supporting call-path evidence (factual, for downstream stages)

| Detail | `file:line` | Verbatim snippet |
|--------|-------------|------------------|
| CLI routes `check-limit` to `is_within_daily_limit` with parsed floats. | `src/paycli/cli.py:36` | `print(transactions.is_within_daily_limit(args.spent, args.amount, args.limit))` |
| `average` subcommand accepts zero-or-more amounts (`nargs="*"`), so an empty list reaches `average_transaction`. | `src/paycli/cli.py:19` | `p_avg.add_argument("amounts", type=float, nargs="*")` |
| CLI routes `average` to `average_transaction`. | `src/paycli/cli.py:34` | `print(transactions.average_transaction(args.amounts))` |
| `export` subcommand passes the raw `path` argument (no validation) to `export_report`. | `src/paycli/cli.py:27` | `p_export.add_argument("path")` |
| CLI routes `export` to `export_report`. | `src/paycli/cli.py:38` | `return export_report(args.path)` |
| `subprocess` is imported at module scope in `report.py`. | `src/paycli/report.py:9` | `import subprocess` |

## 2. Notes

- The seeded-bug comments in source (e.g. `transactions.py:20-22`, `transactions.py:29-30`,
  `report.py:11`, `report.py:18-19`) restate the defects; the factual claims above are drawn from
  the executable lines (`:23`, `:32`, `:21`, `:12`), not the comments.
- `total` (`src/paycli/transactions.py:14`) was read while locating the others; it is not a seeded
  issue and exhibits no documented defect.
- All four issues were located at the expected locations named in `bug-context.md`. None were
  "not found".

## Handoff → research-verifier

Verify each claim by opening the cited line:

- **BUG-A** — `src/paycli/transactions.py:32` — confirm operator is `<` (strict) in
  `return spent + amount < limit`.
- **BUG-B** — `src/paycli/transactions.py:23` — confirm `return sum(amounts) / len(amounts)` has no
  empty-sequence guard.
- **VULN-1** — `src/paycli/report.py:21` — confirm `subprocess.call(f"cat {path} > report.txt", shell=True)`
  interpolates user `path` with `shell=True`.
- **VULN-2** — `src/paycli/report.py:12` — confirm `API_KEY = "sk-live-DEMO0000000000000000000000"`
  is a hardcoded literal.
- Supporting CLI routing: `src/paycli/cli.py:34`, `:36`, `:38` and arg defs `:19`, `:27`.
