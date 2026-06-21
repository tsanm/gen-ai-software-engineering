# Security Verifier Result

**Mode:** Architect (READ-ONLY — report only, no edits made).
**Scope:** Files changed per `fix-summary.md`:
- `src/paycli/transactions.py` (BUG-A, BUG-B — logic)
- `src/paycli/report.py` (VULN-1, VULN-2 — security)

## Seeded-Vulnerability Status

- **VULN-1 (command injection) — REMEDIATED.** `export_report()` no longer builds a
  shell command. `subprocess`/`shell=True` are gone; the function now uses plain
  binary file I/O (`open(...)` + `shutil.copyfileobj`) inside a `try/except OSError`.
  A caller-supplied `path` can no longer inject shell commands. Verified by grep:
  no `subprocess`, no `shell=True` anywhere under `src/`.
- **VULN-2 (hardcoded secret) — REMEDIATED.** The literal
  `sk-live-DEMO0000000000000000000000` no longer appears anywhere under `src/`.
  `API_KEY` is now read from `os.environ.get("PAYCLI_API_KEY", "")`, defaulting to an
  empty string. Verified by grep: the secret literal returns zero matches.

## Findings (descending severity)

### MEDIUM — Arbitrary file overwrite of `report.txt` via relative output path
- **File:** `src/paycli/report.py:23`
- **Description:** The destination is the hardcoded relative path `report.txt`, opened
  in `"wb"` (truncating) mode in the current working directory. Any caller invoking
  `export_report()` unconditionally truncates/overwrites a `report.txt` in CWD. This is
  not injection, but the write target is implicit and uncontrolled by the caller. If CWD
  is attacker-influenced or shared, an existing `report.txt` is destroyed. Low real-world
  impact for a demo CLI, but the output location should be explicit.
- **Remediation:** Make the destination an explicit parameter (e.g.
  `export_report(path: str, dest: str = "report.txt")`) and/or resolve it against a known
  output directory; consider refusing to overwrite without an explicit flag.

### LOW — Source-path traversal / unrestricted read
- **File:** `src/paycli/report.py:23`
- **Description:** `path` is passed directly to `open(path, "rb")` with no validation or
  base-directory containment. A caller can read any file the process can access
  (e.g. `../../etc/passwd`) and copy its contents into `report.txt`. Since the caller
  supplies the path and reads their own output, exposure is bounded, but there is no
  allow-list or canonicalization.
- **Remediation:** If `path` is meant to stay within a known reports directory,
  canonicalize with `os.path.realpath` and verify it is contained under that base before
  opening; otherwise document that arbitrary readable paths are intentionally allowed.

### INFO — `API_KEY` evaluated once at import time
- **File:** `src/paycli/report.py:13`
- **Description:** `API_KEY` is bound at module import. If `PAYCLI_API_KEY` is set after
  import, the change is not picked up (noted in `fix-summary.md` Manual Verification).
  Correct and secure, but a functional gotcha; not a vulnerability.
- **Remediation:** If late/dynamic configuration is needed, read the env var inside the
  function that uses the key rather than at module scope. No change required for security.

### INFO — `API_KEY` is defined but unused in source
- **File:** `src/paycli/report.py:13`
- **Description:** No code in `src/` references `API_KEY` after definition (grep confirms a
  single occurrence). No leakage path (logging, error message, or transmission) was found.
  Good — nothing to flag, recorded for completeness.

### INFO — `transactions.py` changes carry no security impact
- **File:** `src/paycli/transactions.py:19-21, 29`
- **Description:** BUG-B adds an empty-sequence guard (`if not amounts: return 0.0`) and
  BUG-A changes a strict `<` to `<=` boundary. Both are pure arithmetic/logic with no
  untrusted-input, injection, or secret surface. No findings.

## Summary

| Item | Severity | Status |
|------|----------|--------|
| VULN-1 command injection (`export_report`) | — | REMEDIATED |
| VULN-2 hardcoded secret (`API_KEY`) | — | REMEDIATED |
| Arbitrary `report.txt` overwrite | MEDIUM | Open (new-code hardening) |
| Source-path traversal / unrestricted read | LOW | Open (new-code hardening) |
| `API_KEY` import-time eval | INFO | Advisory |
| `API_KEY` unused | INFO | Advisory |
| `transactions.py` logic | INFO | No issue |

No CRITICAL or HIGH findings. Both seeded vulnerabilities (VULN-1, VULN-2) are fully
remediated. The remaining MEDIUM/LOW items are pre-existing characteristics of the new
file-I/O implementation, not regressions, and do not block shipping; they are recommended
hardening for `export_report()`.

## Handoff → unit-test-generator

The changed code is security-clean of the seeded issues. For test generation, cover:
- `export_report()`: success path (returns `0`, `report.txt` written with source bytes);
  failure path (nonexistent/unreadable `path` returns `1` via `OSError`); confirm no shell
  is invoked. If addressing the MEDIUM/LOW notes, add tests asserting the destination path
  and rejecting/handling traversal inputs.
- `API_KEY`: assert it is empty by default and reads `PAYCLI_API_KEY` when set at import.
- `average_transaction([])` returns `0.0`; non-empty average correct.
- `is_within_daily_limit()` boundary: exact-limit spend returns `True` (inclusive),
  over-limit returns `False`.
