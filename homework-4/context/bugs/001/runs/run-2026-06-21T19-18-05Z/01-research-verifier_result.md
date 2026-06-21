# Research Verifier Result — paycli (batch 001)

Architect mode (read-only). Fact-checks `context/bugs/001/research/codebase-research.md`
against `src/` using the **research-quality-measurement** skill. No code was edited.

## 1. Verification Summary
**PASS** — every cited `file:line` resolves and each quoted snippet matches the source
**exactly**. All four core claims (BUG-A, BUG-B, VULN-1, VULN-2) and all five supporting
cross-references confirmed. No discrepancies.

**Research Quality: Verified.**

## 2. Verified Claims
| Claim | `file:line` | Snippet matches? |
|-------|-------------|------------------|
| BUG-A — daily-limit check uses strict `<` (boundary off-by-one) | `src/paycli/transactions.py:32` | yes |
| BUG-B — `average_transaction` divides by `len` with no empty guard → `ZeroDivisionError` | `src/paycli/transactions.py:23` | yes |
| VULN-1 — `export_report` runs `subprocess.call(..., shell=True)` on caller `path` (command injection) | `src/paycli/report.py:21` | yes |
| VULN-2 — hardcoded `API_KEY` secret literal in source | `src/paycli/report.py:12` | yes |
| Supporting: BUG-A call site | `src/paycli/cli.py:36` | yes |
| Supporting: BUG-B call site | `src/paycli/cli.py:34` | yes |
| Supporting: VULN-1 `import subprocess` | `src/paycli/report.py:9` | yes |
| Supporting: VULN-1 export path arg | `src/paycli/cli.py:27` | yes |
| Supporting: VULN-1 path flows to `export_report` | `src/paycli/cli.py:38` | yes |

Snippet evidence (source ↔ research):
- `transactions.py:32` → `    return spent + amount < limit` ✓
- `transactions.py:23` → `    return sum(amounts) / len(amounts)` ✓
- `report.py:21` → `    return subprocess.call(f"cat {path} > report.txt", shell=True)` ✓
- `report.py:12` → `API_KEY = "sk-live-DEMO0000000000000000000000"` ✓
- `report.py:9` → `import subprocess` ✓
- `cli.py:34` → `print(transactions.average_transaction(args.amounts))` ✓
- `cli.py:36` → `print(transactions.is_within_daily_limit(args.spent, args.amount, args.limit))` ✓
- `cli.py:27` → `p_export.add_argument("path")` ✓
- `cli.py:38` → `return export_report(args.path)` ✓

The seed-comment ranges cited in the research Notes also resolve: BUG-B comment at
`transactions.py:20-21`, BUG-A comment at `transactions.py:29-30`, VULN-2 comment at
`report.py:11`, VULN-1 comment at `report.py:18-19` (each within the ±1 docstring range
the research cited). `total()` at `transactions.py:12-14` is present and correctly not
flagged as a defect.

## 3. Discrepancies Found
None.

(Minor, non-blocking: the supporting-context lines 17 & 21 abbreviate the call-site
snippets to `print(...)` — the source lines are indented 8 spaces under the `if/elif`.
This is a quotation of the call expression, not the full line, and does not affect any
claim or its `file:line`. Not counted as a discrepancy.)

## 4. Research Quality Assessment
**Verified.** 100% of claims (4 core + 5 supporting cross-references) resolve to a single
definition with a snippet that matches source character-for-character; there are no wrong
lines, paraphrases, or missing references, so the research is safe to act on.

## 5. References
Files inspected:
- `src/paycli/transactions.py`
- `src/paycli/report.py`
- `src/paycli/cli.py`
- Skill: `.claude/skills/research-quality-measurement.md`
- Input: `context/bugs/001/research/codebase-research.md`

## Handoff -> rca-analyst
Research Quality is **Verified** — the gate is open; proceed to root-cause analysis.
Analyse these confirmed defects (each verified at the exact `file:line` below):

1. **BUG-A** — `src/paycli/transactions.py:32`: `is_within_daily_limit` returns
   `spent + amount < limit`; a spend landing exactly on the limit is wrongly rejected.
   Reached via `cli.py:36`.
2. **BUG-B** — `src/paycli/transactions.py:23`: `average_transaction` returns
   `sum(amounts) / len(amounts)` with no empty guard → `ZeroDivisionError`.
   Reached via `cli.py:34`.
3. **VULN-1** — `src/paycli/report.py:21`: `export_report` runs
   `subprocess.call(f"cat {path} > report.txt", shell=True)` on caller-supplied `path`
   (command injection). Path flows from `cli.py:27` → `cli.py:38`; `import subprocess`
   at `report.py:9`.
4. **VULN-2** — `src/paycli/report.py:12`: hardcoded `API_KEY` secret literal in source.
