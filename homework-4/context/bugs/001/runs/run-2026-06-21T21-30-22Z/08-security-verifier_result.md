# Security Verifier — Report (batch 001)

**Scope:** Independent security review of the files changed per `fix-summary.md`. Report only — no
edits made (enforced by read-only tool scope). Findings verified by reading the actual source, not
by trusting the fix summary.

**Files reviewed (changed):**
- `src/paycli/transactions.py` (Changes 1, 2 — BUG-A `<=` boundary, BUG-B empty-guard)
- `src/paycli/report.py` (Changes 3, 4 — VULN-2 credential, VULN-1 shell injection)

**Files read for call-context (unchanged):** `src/paycli/cli.py` (the `export` subcommand routes
attacker-controlled `path` into `export_report`).

---

## 1. Verdict Summary

| Seeded vuln | Original severity | Status | Evidence (read directly) |
|---|---|---|---|
| **VULN-1** — command injection via `shell=True` | **CRITICAL** | ✅ **REMEDIATED** | `report.py:23-27` uses `shutil.copyfile(path, "report.txt")`; no `subprocess`/`shell=True`/`os.system` anywhere in `src/` (grep: 0 matches). `path` is now passed as a data argument and cannot be interpreted by a shell. |
| **VULN-2** — hardcoded secret in source | **HIGH** | ✅ **REMEDIATED** | `report.py:13` is `API_KEY = os.environ.get("PAYCLI_API_KEY", "")`; literal `sk-live-DEMO…` removed (grep `sk-live`: 0 matches in `src/`). |

**Residual CRITICAL: 0 · Residual HIGH: 0.**

Both seeded vulnerabilities are confirmed fixed by reading the fixed lines. No new CRITICAL/HIGH
issues introduced. The change is **clear to proceed** to test generation. Two LOW and two INFO
defense-in-depth observations follow; none block the merge.

---

## 2. Findings (descending severity)

### LOW-1 — Unvalidated, unconstrained source path (arbitrary local file read into `report.txt`)
- **Location:** `src/paycli/report.py:24` (`shutil.copyfile(path, "report.txt")`); reached from
  `src/paycli/cli.py:38` with fully caller-controlled `args.path`.
- **Description:** `path` is copied with no validation or base-directory confinement, so any readable
  file (e.g. `../../etc/passwd`) can be copied into `report.txt`. This is **not** command injection —
  shell metacharacters are inert now — but it is a classic path-traversal / arbitrary-read shape.
  Impact is bounded because `paycli` is a local CLI running with the invoking user's own privileges
  (the user can already read those files directly), so this is informational-to-low rather than a
  privilege boundary crossing. It would become material if `export_report` were ever exposed through
  a service or higher-privilege context.
- **Remediation:** If reports must stay within a known directory, resolve and confine the path, e.g.
  `base = Path("./reports").resolve(); target = (base / path).resolve()` then verify
  `target.is_relative_to(base)` before copying; otherwise document that arbitrary local read is
  intended for this CLI.

### LOW-2 — Silent empty-credential fallback
- **Location:** `src/paycli/report.py:13` (`os.environ.get("PAYCLI_API_KEY", "")`).
- **Description:** When `PAYCLI_API_KEY` is unset, `API_KEY` is the empty string and the program
  continues silently. The credential is currently unused in this module, so there is no live auth
  bypass — but a future caller that sends `API_KEY` would transmit an empty credential and fail
  open/obscurely instead of failing fast. Defaulting-empty is the correct *non-secret* choice; the
  gap is the lack of a loud failure when the key is genuinely required.
- **Remediation:** When the key is actually consumed, validate at use-time (e.g. raise/exit with a
  clear "PAYCLI_API_KEY not set" message) rather than proceeding with `""`.

### INFO-1 — Fixed relative output path written to CWD
- **Location:** `src/paycli/report.py:24` (destination hardcoded to `"report.txt"`).
- **Description:** Output is written to `report.txt` in the current working directory, silently
  overwriting any existing file of that name. No security boundary crossed; noted for robustness.
- **Remediation:** Consider an explicit/output-dir-relative destination if overwrite-in-CWD is
  undesirable. No action required for this fix.

### INFO-2 — Logic fixes carry no security surface (noted for completeness)
- **Location:** `src/paycli/transactions.py:34` (`<=` boundary) and `:23-24` (`if not amounts: return 0.0`).
- **Description:** Both are pure numeric/logic corrections (BUG-A boundary, BUG-B empty-guard). No
  injection, I/O, secret, or auth surface. `Sequence` typing and value handling are sound; the
  empty-guard removes the prior `ZeroDivisionError` denial-of-service-on-empty-input edge.
- **Remediation:** None.

---

## 3. Remediation Confirmation Detail

- **`except OSError` scope (raised in handoff):** Appropriate, not over-broad. `shutil.copyfile`
  raises `OSError` subclasses for missing/unreadable source and `shutil.SameFileError` (an `OSError`
  subclass) for src==dst — all sensibly mapped to exit code 1. It does **not** swallow
  programming errors like `TypeError`, so the catch is correctly narrow.
- **No shell path remains:** grep over `src/` for `shell=True`, `subprocess`, `os.system`, `eval(`,
  `exec(` → 0 matches.
- **No secret remains:** grep over `src/` for `sk-live` → 0 matches; `API_KEY` sources from env.

---

## 4. References

- `src/paycli/report.py` — reviewed in full (VULN-1, VULN-2 remediations confirmed at lines 13, 23–27).
- `src/paycli/transactions.py` — reviewed in full (lines 23–25, 34).
- `src/paycli/cli.py` — read for caller context of `export_report` (line 38).
- `context/bugs/001/fix-summary.md` — fixer handoff under review.

---

## Handoff → unit-test-generator

Security gate: **PASS.** Both seeded vulnerabilities (VULN-1 command injection, VULN-2 hardcoded
secret) are REMEDIATED, verified by reading the fixed source. Zero residual CRITICAL/HIGH. No re-fix
required — proceed to test generation.

Generate FIRST unit tests for the changed code, and please include security-regression tests that
lock the fixes in:
1. **VULN-1 regression** — `export_report('x; touch /tmp/paycli_pwned')` returns `1` and creates **no**
   side-effect file (injection string treated as a literal, missing path). Assert no shell execution.
2. **VULN-2 regression** — with `PAYCLI_API_KEY` unset, `report.API_KEY == ""`; with it set, the value
   is read from the environment. Assert no `sk-live` literal is importable.
3. **BUG-A boundary** — `is_within_daily_limit(spent, amount, limit)` is `True` when `spent+amount == limit`.
4. **BUG-B empty-guard** — `average_transaction([]) == 0.0` (no `ZeroDivisionError`).

Optional (LOW-1, defense-in-depth, non-blocking): a test documenting current path behavior if path
confinement is later added.
