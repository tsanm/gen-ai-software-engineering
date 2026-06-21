# Research Verifier — Verified Research (batch 001)

Fact-check of `context/bugs/001/research/codebase-research.md` against `src/`, with a Research
Quality level assigned per the `research-quality-measurement` skill. Truth gate only — no root-cause
analysis, no fixes, no edits.

## 1. Verification Summary

- **Overall:** PASS.
- **Research Quality level:** **Verified**.
- All 4 primary findings (BUG-A, BUG-B, VULN-1, VULN-2) and all 6 supporting call-path claims
  resolve to a real `file:line`, and every quoted snippet matches the source verbatim (modulo
  leading indentation, which is not part of the quoted token). Zero discrepancies.

## 2. Verified Claims

| Claim | `file:line` | Snippet matches? |
|-------|-------------|------------------|
| BUG-A — `is_within_daily_limit` uses strict `<`; equal sum is rejected. `return spent + amount < limit` | `src/paycli/transactions.py:32` | yes |
| BUG-B — `average_transaction` divides by `len` with no empty-sequence guard. `return sum(amounts) / len(amounts)` | `src/paycli/transactions.py:23` | yes |
| VULN-1 — `export_report` interpolates `path` into a shell string run with `shell=True`. `return subprocess.call(f"cat {path} > report.txt", shell=True)` | `src/paycli/report.py:21` | yes |
| VULN-2 — hardcoded secret literal assigned to `API_KEY`. `API_KEY = "sk-live-DEMO0000000000000000000000"` | `src/paycli/report.py:12` | yes |
| CLI routes `check-limit` to `is_within_daily_limit`. `print(transactions.is_within_daily_limit(args.spent, args.amount, args.limit))` | `src/paycli/cli.py:36` | yes |
| `average` accepts zero-or-more amounts (`nargs="*"`). `p_avg.add_argument("amounts", type=float, nargs="*")` | `src/paycli/cli.py:19` | yes |
| CLI routes `average` to `average_transaction`. `print(transactions.average_transaction(args.amounts))` | `src/paycli/cli.py:34` | yes |
| `export` passes raw `path` (no validation). `p_export.add_argument("path")` | `src/paycli/cli.py:27` | yes |
| CLI routes `export` to `export_report`. `return export_report(args.path)` | `src/paycli/cli.py:38` | yes |
| `subprocess` imported at module scope in `report.py`. `import subprocess` | `src/paycli/report.py:9` | yes |

## 3. Discrepancies Found

None.

> Note (non-discrepancy): quoted snippets omit the source's leading 4-space indentation. This is
> expected for inline `file:line` quotation and does not constitute a mismatch — the executable
> tokens are identical to source.

## 4. Research Quality Assessment

**Verified.** 100% of claims (4 primary + 6 supporting) have a resolving `file:line` that I opened
directly, and each quoted snippet matches the source exactly with zero discrepancies — meeting the
skill's `Verified` criteria. The research also correctly distinguishes the executable defect lines
(`:23`, `:32`, `:21`, `:12`) from the descriptive seeded-bug comments, so downstream stages will act
on real behaviour rather than narration.

## 5. References

Source files inspected during verification:

- `src/paycli/transactions.py`
- `src/paycli/report.py`
- `src/paycli/cli.py`

Research artifact verified:

- `context/bugs/001/research/codebase-research.md`

## Handoff → rca-analyst

Research is **VERIFIED** (quality level: Verified; zero discrepancies). The pipeline may proceed to
root-cause analysis. Derive the root cause from this report using the 5 Whys method, grounding every
step in the confirmed `file:line` evidence:

- **BUG-A** — `src/paycli/transactions.py:32` — strict `<` boundary error; sum equal to `limit` is
  wrongly rejected. Reached via `cli.py:36`.
- **BUG-B** — `src/paycli/transactions.py:23` — unguarded `len(amounts)` division; empty input
  (allowed by `cli.py:19` `nargs="*"`, routed at `cli.py:34`) raises `ZeroDivisionError`.
- **VULN-1** — `src/paycli/report.py:21` — command injection via `shell=True` f-string on raw
  `path` (unvalidated at `cli.py:27`, routed at `cli.py:38`).
- **VULN-2** — `src/paycli/report.py:12` — hardcoded secret literal in source.
