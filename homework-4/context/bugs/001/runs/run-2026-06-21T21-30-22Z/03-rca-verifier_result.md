# RCA Verifier — Verified RCA (batch 001)

Critical review of `context/bugs/001/rca.md`. Every cited `file:line` was opened and confirmed
against source; each 5 Whys chain was judged fundamental-vs-symptom; affected symbols were grepped
for side effects. Report only — no code edited, no plan written.

Revision attempt: **1** (first pass).

---

## 1. Verdict

**VERIFIED WITH NOTES.**

All four root causes are correct and reach a **fundamental** cause (specification / contract /
design / lifecycle), and **every code `file:line` in the RCA matches source exactly**. Two notes,
both at the deepest (Why-5) step, do **not** block planning because the fundamental cause for each
is already reached earlier in the chain (Why-3/Why-4) and the implied fix direction is unaffected:

- **N1 (factual — must correct in narrative):** BUG-A Why-5 and BUG-B Why-5 both assert an
  *absence* of tests ("no boundary test", "no test exercising `average_transaction([])`"). This is
  **false**. `tests/test_baseline.py` already contains both:
  - `test_limit_exactly_at_limit_is_allowed` — `tests/test_baseline.py:12-14`
    (`is_within_daily_limit(60.0, 40.0, 100.0) is True`, i.e. `60+40 == 100 == limit`) is exactly
    the boundary the RCA says is untested.
  - `test_average_of_empty_is_zero` — `tests/test_baseline.py:25-27`
    (`average_transaction([]) == 0`) is exactly the empty-input case the RCA says is untested.

  These are the **RED baseline** tests (TDD; failing pre-fix per `tests/test_baseline.py:1-7` and
  the `08bff…` "RED baseline tests" commit). So the correct framing is the opposite of the RCA's:
  a failing signal **does exist** — the defect persists *despite* a RED test, not for lack of one.
  This strengthens the root cause; it does not weaken it. The narrative at BUG-A Why-5 and
  BUG-B Why-5 should be corrected before it propagates into the plan/test stages.

- **N2 (minor):** VULN-2 Why-5 cites the CLAUDE.md "No secrets in committed code" policy as
  un-enforced "in code". Accurate as written (no in-repo gate blocks the literal); noting only that
  the project quality gate *does* list `bandit`, so "no blocking signal" is true at commit time but
  a `bandit` gate is configured for CI. No correction required.

Neither note changes a fix direction. No critical issue remains → proceed to CHECKPOINT 1.

---

## 2. 5 Whys Depth

| Chain | Depth | Reaches fundamental? | Notes |
|-------|-------|----------------------|-------|
| BUG-A | 5 | **Yes** — Why-3/Why-4: intended *inclusive* upper bound (`<=`) never modelled; boundary spec ("is the limit itself allowed?") never disambiguated. Fundamental = unmodelled boundary condition, not the `<` symptom. | Why-1/2 (symptom: `<` excludes endpoint) correctly deepen to spec gap. **N1**: Why-5 "(absence)" evidence is wrong — `tests/test_baseline.py:12-14` tests this boundary. Fundamental cause stands without Why-5. |
| BUG-B | 5 | **Yes** — Why-3/Why-4: implicit precondition (`len ≥ 1`) never reconciled with public contract `nargs="*"` which admits `[]`. Fundamental = contract/precondition gap. | Sound chain from symptom (`/0`) to contract mismatch. **N1**: Why-5 "(absence)" evidence is wrong — `tests/test_baseline.py:25-27` tests `average_transaction([])`. Fundamental cause stands without Why-5. |
| VULN-1 | 5 | **Yes** — Why-5: design choice to invoke a shell (`shell=True`) for a file op while treating `path` as trusted; no layer separates command from argument. Fundamental = erased code/data boundary. | Strong, monotonically-deepening chain (symptom → shell parsing → unfiltered input → trusted-by-default → no safe pattern). Severity **Critical** confirmed. |
| VULN-2 | 5 | **Yes** — Why-4: no configuration/secret-injection seam; credential lifecycle bound to code rather than environment. Fundamental = missing separation of secret lifecycle from code. | **N2** at Why-5 (policy/enforcement nuance) — non-blocking. Chain reaches fundamental at Why-4 regardless. |

All four chains have depth 5 (≥3 required; ≥5 for complex) and reach a fundamental cause **before**
the Why-5 step in question, so N1/N2 are narrative corrections, not depth failures.

---

## 3. Execution Path Verification

Every `file:line` cited in `rca.md` opened and compared to source.

| `file:line` (RCA) | Claimed content | Exists? | Matches? |
|-------------------|-----------------|---------|----------|
| `transactions.py:14` | `return sum(amounts)` (`total`, unaffected) | Yes | Yes |
| `transactions.py:17-23` | `average_transaction` body + docstring | Yes | Yes |
| `transactions.py:20-21` | docstring intent "returning 0" | Yes | Yes |
| `transactions.py:23` | `return sum(amounts) / len(amounts)` (BUG-B fault) | Yes | Yes |
| `transactions.py:26-32` | `is_within_daily_limit` body/docstring | Yes | Yes |
| `transactions.py:27` | docstring "within ``limit``" | Yes | Yes |
| `transactions.py:29-30` | docstring "strict ``<`` … Should be ``<=``" | Yes | Yes |
| `transactions.py:32` | `return spent + amount < limit` (BUG-A fault) | Yes | Yes |
| `report.py:9` | `import subprocess` | Yes | Yes |
| `report.py:12` | `API_KEY = "sk-live-DEMO0000000000000000000000"` (VULN-2 fault) | Yes | Yes |
| `report.py:15` | `def export_report(path: str) -> int:` | Yes | Yes |
| `report.py:21` | `return subprocess.call(f"cat {path} > report.txt", shell=True)` (VULN-1 fault) | Yes | Yes |
| `cli.py:19` | `p_avg.add_argument("amounts", type=float, nargs="*")` | Yes | Yes |
| `cli.py:27` | `p_export.add_argument("path")` | Yes | Yes |
| `cli.py:34` | `print(transactions.average_transaction(args.amounts))` | Yes | Yes |
| `cli.py:36` | `print(transactions.is_within_daily_limit(args.spent, args.amount, args.limit))` | Yes | Yes |
| `cli.py:38` | `return export_report(args.path)` | Yes | Yes |

**Result: 17/17 cited code locations exist and match verbatim.** The only inaccuracy is the
*interpretation* at BUG-A/BUG-B Why-5 (claimed test absence), not a `file:line` mismatch — see N1.

---

## 4. Side Effects

Grepped each affected symbol across the repo (`*.py`) for other uses:

| Symbol | Other uses | Side-effect risk of implied fix |
|--------|-----------|--------------------------------|
| `is_within_daily_limit` (BUG-A `<`→`<=`) | `cli.py:36`; `tests/test_baseline.py:14,18,22` | **Low.** Only the exact-equal endpoint changes: `:14` (60+40==100) flips RED→GREEN as intended; `:18` (60+41=101>100→False) and `:22` (60+39=99<100→True) are unaffected. |
| `average_transaction` (BUG-B empty guard) | `cli.py:34`; `tests/test_baseline.py:27,31` | **Low.** Guard targets `[]` only (`:27` RED→GREEN); non-empty path `:31` (`[10,20,30]→20.0`) unchanged. Return type stays `float`. |
| `export_report` (VULN-1 no-shell rewrite) | `cli.py:38` (`return export_report(...)`) | **Low–Medium.** No existing test; rewrite must preserve the `int` status contract consumed at `cli.py:38` and still produce `report.txt`. Flagged in RCA §6 — correct. |
| `API_KEY` (VULN-2 → env var) | **Zero readers** — assigned only at `report.py:12`, never referenced elsewhere. | **Low.** Regression surface is import-time only; RCA §6 claim "no current caller reads `API_KEY`" is **confirmed** by grep. |

**Overall side-effect risk: Low.** All four issues are independent (two in `transactions.py`, two
in `report.py`); no shared state; `total()` (`transactions.py:14`) is untouched. The RCA Risks
section (§6) is accurate and complete.

---

## 5. References

Source opened during verification:
- `src/paycli/transactions.py` (full)
- `src/paycli/report.py` (full)
- `src/paycli/cli.py` (full)
- `tests/test_baseline.py` (full) — basis for note **N1**

Artifacts reviewed:
- `context/bugs/001/rca.md` (under review)
- `context/bugs/001/research/verified-research.md` (RCA's grounding source)

---

## Handoff → next

**Verdict: VERIFIED WITH NOTES → proceed to CHECKPOINT 1 (human review) → bug-planner.**

The RCA is sound: 4/4 root causes are fundamental, 17/17 code `file:line`s verify verbatim, and the
side-effect surface is Low with `API_KEY` confirmed to have zero readers. The plan may be built on
these root causes and fix directions:

- **BUG-A** — `transactions.py:32` — change exclusive `<` to inclusive `<=`. Locked by RED baseline
  `tests/test_baseline.py:12-14`.
- **BUG-B** — `transactions.py:23` — guard the empty sequence, return `0`/`0.0` per docstring
  (`transactions.py:20-21`). Locked by RED baseline `tests/test_baseline.py:25-27`.
- **VULN-1** — `report.py:21` — remove `shell=True`; use a no-shell file copy / argument vector;
  preserve the `int` status returned to `cli.py:38`.
- **VULN-2** — `report.py:12` — read the credential from the environment (`os.environ`); decide
  fail-fast vs. default on absence; no runtime caller depends on the literal.

**Note carried forward (N1 — non-blocking):** The RCA's BUG-A/BUG-B Why-5 rows claim the boundary
and empty-input tests are *absent*; they actually **exist** as RED baseline tests
(`tests/test_baseline.py:12-14` and `:25-27`). The planner/unit-test-generator must **not** create
duplicate tests for these cases — extend the existing RED baseline (the unit-test-generator should
add the new VULN-1 injection-blocked test, per `tests/test_baseline.py:5-6`). The RCA narrative
should be corrected to reflect a failing signal that exists rather than one that is missing; this
does not change any fix.
