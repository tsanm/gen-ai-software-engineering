# RCA Verifier Result — paycli (batch 001)

Architect mode (read-only). Validates each **5-Whys** chain in
`context/bugs/001/rca.md` for **logical soundness** (each *Why* is genuinely caused by the
one below it) and **evidence** (every claim ties to a confirmed `file:line`). No code was
edited; no fixes proposed.

**Sources re-confirmed at the cited lines:**
- `transactions.py:32` → `    return spent + amount < limit` ✓
- `transactions.py:27` (contract) → `"...keeps the day's total within ``limit``."` ✓
- `transactions.py:23` → `    return sum(amounts) / len(amounts)` ✓
- `report.py:21` → `    return subprocess.call(f"cat {path} > report.txt", shell=True)` ✓
- `report.py:9` → `import subprocess` ✓
- `report.py:12` → `API_KEY = "sk-live-DEMO0000000000000000000000"` ✓
- `cli.py:19` → `p_avg.add_argument("amounts", type=float, nargs="*")` ✓
- `cli.py:27` → `p_export.add_argument("path")` · `cli.py:38` → `return export_report(args.path)` ✓
- `cli.py:36` → `print(transactions.is_within_daily_limit(...))` ✓

---

## Per-chain verdicts

### BUG-A — boundary off-by-one in daily-limit check — **PASS**
- **Soundness:** Each step is caused by the next-deeper one. Symptom (exact-limit rejected)
  ← `<` excludes the boundary (Why 1) ← operator chosen as `<` not `<=` vs. the "within"
  contract (Why 2) ← inclusive semantics never translated (Why 3) ← no boundary test to
  signal it (Why 4) ← "on the limit is allowed" never an explicit acceptance criterion (Why 5).
  No leaps; Why 4/Why 5 correctly separate *implementation* mismatch from *missing spec/test*.
- **Evidence:** `<` at `transactions.py:32` confirmed; contract wording at `:27` confirmed;
  the seed comment at `:29-30` independently states "Should be `<=`." Worked example
  (`100 < 100 → False`) is arithmetically correct.
- **Root cause:** Inclusive upper-bound rule implemented with an exclusive operator, unpinned
  by any boundary test — **evidence-backed and actionable** (`<` → `<=`).
- **Notes:** Sound and minimal. Root cause names the exact fix lever without prescribing it.

### BUG-B — unguarded division by zero in average — **PASS**
- **Soundness:** Crash on empty input (symptom) ← `len([])==0` divides (Why 1) ← empty list
  is a *reachable* input via `nargs="*"` (Why 2) ← no guard before dividing (Why 3) ← contract
  never defines an empty-input return (Why 4) ← no test exercises the empty path (Why 5).
  Causal links hold; Why 2 correctly establishes reachability rather than asserting it.
- **Evidence:** Division at `transactions.py:23` confirmed; `nargs="*"` confirmed at
  `cli.py:19` (RCA cites `cli.py:19` — correct) and routed at `cli.py:34`. Seed comment at
  `:20-21` corroborates the empty-sequence `ZeroDivisionError`.
- **Root cause:** Unhandled empty-sequence edge case reachable from the CLI, with no contract
  or test — **evidence-backed and actionable** (add a guard, define empty result).
- **Notes:** Sound. Reachability is proven, not assumed — strengthens the chain.

### VULN-1 — command injection via `shell=True` — **PASS**
- **Soundness:** Arbitrary command execution (symptom) ← string run under `shell=True` (Why 1)
  ← `path` interpolated with no quoting/validation (Why 2) ← external CLI arg treated as
  trusted (Why 3) ← a shell used for a task plain file I/O could do (Why 4) ← secure-by-default
  practice not applied / no review flagged it (Why 5). Each step deepens the prior cause;
  Why 4 (unnecessary shell) and Why 5 (no control) are distinct, non-redundant roots.
- **Evidence:** `shell=True` f-string at `report.py:21` confirmed; `import subprocess` at
  `:9` confirmed; untrusted flow `cli.py:27 → :38` confirmed. Injection example
  (`path = "x; rm -rf ."`) matches the seed comment at `:18-19`.
- **Root cause:** Shell command built from untrusted input and executed with `shell=True`,
  no arg list/validation, shell unneeded — **evidence-backed and actionable**.
- **Notes:** Sound. Captures both the proximate (interpolation) and design (unneeded shell) causes.

### VULN-2 — hardcoded secret in source — **PASS**
- **Soundness:** Secret exposed (symptom) ← literal assigned in module source (Why 1) ←
  embedded inline rather than supplied at runtime (Why 2) ← no external config lookup exists
  (Why 3) ← config not separated from code (Why 4) ← no policy/scan prevents committing
  secrets (Why 5). Chain moves cleanly from artifact → practice → missing control.
- **Evidence:** `API_KEY = "sk-live-DEMO…"` at `report.py:12` confirmed. The "no external
  lookup" claim is independently verifiable: `report.py` imports only `subprocess` — there is
  **no** `os`/`os.environ`/config import, so Why 3 holds against source.
- **Root cause:** Secret stored in source instead of injected from env/secret store; missing
  config boundary and control — **evidence-backed and actionable** (move to env var).
- **Notes:** Sound. Why 3 is corroborated by the absence of any config import in the module.

---

## Overall verdict — **PASS (4 / 4 chains valid)**

All four 5-Whys chains are logically sound — each *Why* is genuinely caused by the next, with
no circular reasoning, no skipped links, and a clean progression from symptom → proximate
cause → systemic root (missing test/spec/control). Every factual claim resolves to a
re-confirmed `file:line`, and each root cause is specific, evidence-backed, and actionable.
The seed comments at `transactions.py:20-21`/`:29-30` and `report.py:11`/`:18-19` independently
corroborate all four root causes. **No chain is gated; the pipeline may proceed to CHECKPOINT 1.**

---

## Handoff -> bug-planner

All four validated root causes proceed to planning. Pin each fix to the confirmed line:

1. **BUG-A** — `src/paycli/transactions.py:32`: change `<` to `<=` so an exact-limit spend is
   allowed; anchor with a boundary test at `spent + amount == limit`.
2. **BUG-B** — `src/paycli/transactions.py:23`: guard the empty sequence (define the empty
   result, e.g. return `0`) before dividing; cover the empty-input path with a test.
3. **VULN-1** — `src/paycli/report.py:21`: remove `shell=True`; avoid the shell entirely (use
   Python file I/O or `subprocess` with an argument list); validate/contain `path`.
4. **VULN-2** — `src/paycli/report.py:12`: stop storing the secret in source; load `API_KEY`
   from the environment / a secret store (per CLAUDE.md "No secrets in committed code").

Gate status: **open** — proceed to CHECKPOINT 1 (human review of `verified-rca.md`).
