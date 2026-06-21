# Security Verifier Result — paycli batch 001

**Run:** run-2026-06-21T19-34-27Z
**Mode:** Architect (READ-ONLY — report only, no edits)
**Input:** `context/bugs/001/fix-summary.md` + changed files
**Scope reviewed:**
- `src/paycli/report.py` (changed: docstring; security surface: `export_report`, `API_KEY`)
- `src/paycli/transactions.py` (changed: docstring; security surface: comparisons/guards)
- `src/paycli/cli.py` (caller of `export_report` — reviewed for tainted-input flow)
- `src/paycli/__main__.py` (entry point)

---

## Verdict Summary

| Defect | Status |
|--------|--------|
| **VULN-1 — command injection in `export_report`** | ✅ **REMEDIATED** |
| **VULN-2 — hardcoded secret `API_KEY`** | ✅ **REMEDIATED** (no literal secret present) |

No CRITICAL or HIGH findings. Three INFO observations follow.

---

## Findings (descending severity)

### INFO-1 · Arbitrary file read via unvalidated `path` argument
- **`src/paycli/report.py:12,19`** — `export_report(path)` opens any caller-supplied path
  (`open(path, "rb")`) and copies it into `report.txt`. There is no allowlist, base-directory
  confinement, or symlink check, so a user can read any file the process can access
  (e.g. `python -m paycli export /etc/passwd`).
- **Assessment:** For a local single-user CLI invoked with the user's own privileges this is the
  *intended* "copy a file" behavior, not a privilege boundary crossing — hence INFO, not a vuln.
- **Remediation (optional, defense-in-depth):** if this is ever exposed to untrusted input,
  resolve with `os.path.realpath` and confine to an allowed base directory before opening.

### INFO-2 · Fixed-name output overwrites `report.txt` in the current working directory
- **`src/paycli/report.py:19`** — the destination `"report.txt"` is a hardcoded relative path;
  each export silently truncates/overwrites any existing `report.txt` in CWD.
- **Assessment:** No traversal in the *destination* (constant name), so impact is limited to the
  CWD; data-loss/footgun rather than a security boundary issue. INFO.
- **Remediation (optional):** make the output path explicit/configurable, or refuse to overwrite.

### INFO-3 · `API_KEY` defaults to empty string with no presence check
- **`src/paycli/report.py:9`** — `API_KEY = os.environ.get("PAYCLI_API_KEY", "")`. The env-var
  pattern is correct (no secret in source). The empty default is an availability/correctness
  concern, not a security weakness; note that `API_KEY` is currently never *used* (loaded but not
  read/compared elsewhere), so there is no insecure-comparison or secret-leak path.
- **Remediation (optional):** when the key is actually consumed, fail closed if it is unset rather
  than proceeding with `""`.

---

## VULN-1 — Command Injection: **REMEDIATED**

**Evidence the injection vector is closed:**
- `export_report` (`src/paycli/report.py:12-23`) uses pure Python file I/O —
  `open(path, "rb")` + `open("report.txt", "wb")` + `shutil.copyfileobj(src, dst)`.
- No `subprocess`, `os.system`, `os.popen`, `shell=True`, `eval`, or `exec` anywhere in `src`
  (repo-wide grep returned **only** the `API_KEY` env line — no shell/exec sinks).
- Taint flow confirmed: CLI `export` arg (`src/paycli/cli.py:26-27,37-38`) → `export_report(path)`
  → `open(path, ...)`. The tainted value reaches a filesystem-open sink only, never a shell, so
  shell metacharacters in `path` (`;`, `&&`, `$()`, backticks) are treated as literal filename
  bytes. `path="x; touch pwned.txt"` simply fails to open and returns 1 — no command executes.
- Consistent with fix-summary: `bandit -r src -ll` → 0 HIGH; injection probe created no `pwned.txt`.

## VULN-2 — Hardcoded Secret: **REMEDIATED (not present)**

**Evidence:**
- `src/paycli/report.py:9` reads from the environment: `os.environ.get("PAYCLI_API_KEY", "")`.
- Repo-wide grep for `sk-live-` and `API_KEY *= *["']<literal>` found **no** secret literal in
  `src/paycli/`. No credential is committed.

---

## Other security checks (no findings)

- **Injection (SQL/OS/template):** none — no DB, no shell, no template engine in scope.
- **Insecure comparisons:** no secret/HMAC/token comparison exists; `is_within_daily_limit`
  uses a numeric `<=` (business rule, not a security comparison) — N/A.
- **Input validation:** numeric CLI args are coerced via `argparse type=float`
  (`src/paycli/cli.py:16,19,22-24`), which rejects non-numeric input cleanly; `path` is the only
  free-form input (see INFO-1).
- **Unsafe deserialization / dynamic import:** none (`no pickle/yaml.load/__import__`).
- **Dependencies:** changed modules import only stdlib (`os`, `shutil`, `argparse`,
  `collections.abc`) — no third-party attack surface introduced by this change.
- **XSS/CSRF:** not applicable (offline CLI, no web surface).

---

## Overall

**PASS — safe to proceed.** Both seeded vulnerabilities (VULN-1 command injection, VULN-2
hardcoded secret) are remediated in the working tree. Remaining items are INFO-level
defense-in-depth notes appropriate to a local CLI; none block shipping.

---

## Handoff → unit-test-generator

- **Owed FIRST test:** `test_injection_blocked` for `export_report` (VULN-1) — assert that a
  `path` containing shell metacharacters (e.g. `"x; touch pwned.txt"`) creates **no** side-effect
  file and returns `1`. Do not duplicate existing `tests/test_baseline.py` cases.
- **Suggested additional coverage (optional, supports INFO findings):**
  - `export_report` returns `1` on a non-existent / unreadable source path (OSError branch,
    `report.py:21-22`).
  - `export_report` returns `0` and writes `report.txt` for a valid source (happy path).
  - `API_KEY` falls back to `""` when `PAYCLI_API_KEY` is unset (env-var behavior).
- **No code changes requested.** Security review is report-only; INFO items are optional hardening,
  not required for the gate.
