# Bug Researcher Result — paycli (batch 001)

**Run:** run-2026-06-21T19-34-27Z
**Mode:** Architect (read-only). Files opened: `src/paycli/transactions.py`, `src/paycli/report.py`, `src/paycli/cli.py`.

## ⚠️ Critical finding — seeded defects are NOT present in the current source

The `bug-context.md` seed describes four intentional defects (BUG-A, BUG-B, VULN-1, VULN-2).
I opened every cited location. **None of the four defects exists in the current working-tree
source** — each location already contains the *fixed* form described under "Expected after the
pipeline." The git status corroborates this: `src/paycli/transactions.py` and
`src/paycli/report.py` are both shown as modified (`M`) relative to the seeded baseline commit
`08dfb7f` ("seeded BUG-A/BUG-B + VULN-1/2").

I am reporting what **exists** (the Architect contract), not what the seed predicts. Downstream
stages must treat these as **already-remediated**, not as live bugs to fix.

## 1. Findings

| Issue | Seed claim (defect) | `file:line` | Verbatim snippet at that location | Present? |
|-------|--------------------|-------------|-----------------------------------|----------|
| BUG-A | `is_within_daily_limit` uses strict `<`; spend exactly at limit wrongly rejected | `src/paycli/transactions.py:29` | `    return spent + amount <= limit` | **No — already fixed.** Code uses inclusive `<=`. |
| BUG-B | `average_transaction` divides by `len` with no empty guard → `ZeroDivisionError` | `src/paycli/transactions.py:19-21` | `    if not amounts:` / `        return 0.0` / `    return sum(amounts) / len(amounts)` | **No — already fixed.** Empty guard returns `0.0`. |
| VULN-1 | `export_report` runs `subprocess.call(f"cat {path} …", shell=True)` on user input (B602) | `src/paycli/report.py:22-27` | `    try:` / `        with open(path, "rb") as src, open("report.txt", "wb") as dst:` / `            shutil.copyfileobj(src, dst)` / `    except OSError:` / `        return 1` / `    return 0` | **No — already fixed.** Plain file I/O, no shell, no `subprocess` import. |
| VULN-2 | `report.API_KEY` is a hardcoded secret literal committed in source | `src/paycli/report.py:13` | `API_KEY = os.environ.get("PAYCLI_API_KEY", "")` | **No — already fixed.** Read from environment, no literal. |

### Supporting evidence (verbatim, with line numbers)

**`src/paycli/transactions.py`**
- L17-21 `average_transaction`:
  ```python
  def average_transaction(amounts: Sequence[float]) -> float:
      """Return the average transaction amount; 0.0 for an empty sequence."""
      if not amounts:
          return 0.0
      return sum(amounts) / len(amounts)
  ```
- L24-29 `is_within_daily_limit`:
  ```python
  def is_within_daily_limit(spent: float, amount: float, limit: float) -> bool:
      """Return True if charging ``amount`` keeps the day's total within ``limit``.

      A spend that lands exactly on ``limit`` is allowed (inclusive upper bound).
      """
      return spent + amount <= limit
  ```

**`src/paycli/report.py`**
- L9-13 imports + key:
  ```python
  import os
  import shutil

  # API key is read from the environment, never committed to source.
  API_KEY = os.environ.get("PAYCLI_API_KEY", "")
  ```
- L16-27 `export_report`:
  ```python
  def export_report(path: str) -> int:
      ...
      try:
          with open(path, "rb") as src, open("report.txt", "wb") as dst:
              shutil.copyfileobj(src, dst)
      except OSError:
          return 1
      return 0
  ```
  No `subprocess` import anywhere in the module; module docstring (L1-5) and code comment (L19-20)
  both assert "No shell is involved."

**`src/paycli/cli.py`** — dispatcher only; no defect cited or found. `export` → `export_report(args.path)` (L37-38).

## 2. Notes (ambiguities)

- **The seed and the source disagree.** `bug-context.md` documents defects that the current
  source does not contain. Possible explanations: (a) the four fixes were already applied in the
  working tree (consistent with the `M` git status on both files and the descriptive "already
  fixed" docstrings/comments that read like post-fix narration); (b) this run is being executed
  against an already-completed batch. I cannot run `git`/`diff` (read-only Architect tools:
  Read/Grep/Glob), so I cannot show the pre-fix baseline here — but the modified-file status plus
  the inclusive comments are strong evidence the remediation already happened.
- **Docstrings are written in the post-fix voice.** E.g. `report.py` L17-20 states "No shell is
  involved, so a caller-supplied `path` cannot inject commands." These describe the fixed state,
  not the seeded state — downstream stages should not mistake them for the original seed.
- If the intent was to research the *seeded* (pre-fix) code, the pipeline likely needs to be run
  against baseline commit `08dfb7f` (or the staged changes reverted) before this stage.

## Handoff → research-verifier

Verify the following `file:line` claims against current source. For each, the expectation is the
**fixed** form (defect absent):

1. `src/paycli/transactions.py:29` — `return spent + amount <= limit` (BUG-A fixed: inclusive `<=`, not strict `<`).
2. `src/paycli/transactions.py:19-21` — empty guard `if not amounts: return 0.0` precedes the division (BUG-B fixed).
3. `src/paycli/report.py:22-27` — `open(...)` + `shutil.copyfileobj`, **no** `subprocess`/`shell=True` (VULN-1 fixed).
4. `src/paycli/report.py:13` — `API_KEY = os.environ.get("PAYCLI_API_KEY", "")`, no literal secret (VULN-2 fixed).

**Decision required downstream:** confirm whether this batch is being re-run over already-fixed
code. If so, RCA/plan/fix stages have nothing to change; if the goal is to remediate the *seeded*
baseline, re-run the pipeline against commit `08dfb7f` first.
