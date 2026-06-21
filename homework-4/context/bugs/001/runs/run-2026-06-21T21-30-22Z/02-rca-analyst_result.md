# RCA Analyst — Root-Cause Analysis (batch 001)

Five-Whys root-cause analysis of the four verified issues, grounded **only** in
`context/bugs/001/research/verified-research.md` (Research Quality: **Verified**, zero
discrepancies) and confirmed against source. Each step cites `file:line`. No fixes implemented —
analysis only.

---

## 1. Executive Summary

| ID | Root cause (one line) |
|----|------------------------|
| BUG-A | A **strict `<`** boundary operator encodes the wrong specification of "within limit" — the inclusive upper bound (`<=`) was never modelled, so an exact-limit spend is rejected. `src/paycli/transactions.py:32` |
| BUG-B | The function assumes a **non-empty domain** (`len ≥ 1`) but its public contract (`nargs="*"`) admits the empty list, so `len(amounts) == 0` makes the division undefined. `src/paycli/transactions.py:23` |
| VULN-1 | The path is treated as **trusted data** and composed into a string interpreted by a shell (`shell=True`), so caller input crosses a code/data boundary. `src/paycli/report.py:21` |
| VULN-2 | A live-looking credential is **embedded as a source literal** because no configuration/secret-injection seam exists; the secret's lifecycle was bound to the code. `src/paycli/report.py:12` |

---

## 2. BUG-A — Off-by-one daily-limit boundary

### Symptom Analysis
- **Severity:** High. Silent incorrect business decision — a legitimate spend that exactly reaches
  the daily limit is rejected as over-limit.
- **Impact:** Every boundary-equal transaction (`spent + amount == limit`) returns `False` when it
  should return `True`. No error is raised, so the defect is invisible without a boundary test.

### Fault Localization
- **Entry point:** `check-limit` subcommand → `src/paycli/cli.py:36`
  `print(transactions.is_within_daily_limit(args.spent, args.amount, args.limit))`
- **Execution path:** `cli.main` → `is_within_daily_limit(spent, amount, limit)`
- **Fault point:** `src/paycli/transactions.py:32` — `return spent + amount < limit`

### 5 Whys
| # | Why? | Because… | Evidence (`file:line`) |
|---|------|----------|------------------------|
| 1 | Why is an exact-limit spend rejected? | The result is `spent + amount < limit`, which is `False` when the sum equals `limit`. | `src/paycli/transactions.py:32` |
| 2 | Why does the code use strict `<`? | The boundary case (sum == limit) was treated as "over" rather than "within" — the operator excludes the endpoint. | `src/paycli/transactions.py:32` |
| 3 | Why was the endpoint excluded? | "Within `limit`" was implemented as the wrong relation; the intended **inclusive** upper bound (`<=`) was not encoded. The docstring states the endpoint should pass. | `src/paycli/transactions.py:27,29-30` |
| 4 | Why was the intended inclusive bound not encoded? | The specification of "within" (inclusive vs. exclusive of the limit) was never disambiguated into a test or assertion at the boundary, so `<` and `<=` were interchangeable to the author. | `src/paycli/transactions.py:26-32` (no boundary check present) |
| 5 | Why was the boundary specification never pinned down? | There is no FIRST/boundary unit test asserting behaviour at `spent + amount == limit`, so the off-by-one had no failing signal to catch it. | (absence) verified-research.md §2 routes only the call path; no boundary test cited |

**Root Cause Statement:** The function encodes "within limit" with an **exclusive** comparison
(`<`) when the contract requires an **inclusive** one (`<=`). The fundamental cause is an
unspecified/unmodelled boundary condition — "is the limit itself allowed?" was never resolved into
the operator or a guarding test, so the endpoint was silently excluded. (`transactions.py:32`)

---

## 3. BUG-B — Empty-input division (`ZeroDivisionError`)

### Symptom Analysis
- **Severity:** High. `average` with no amounts crashes the CLI with an unhandled
  `ZeroDivisionError` instead of returning a sensible value (e.g. `0`).
- **Impact:** Any invocation that supplies zero amounts (a valid input per the CLI grammar) aborts
  the program.

### Fault Localization
- **Entry point:** `average` subcommand → `src/paycli/cli.py:34`
  `print(transactions.average_transaction(args.amounts))`
- **Execution path:** `cli.main` → `average_transaction(amounts)` with `amounts == []`
- **Fault point:** `src/paycli/transactions.py:23` — `return sum(amounts) / len(amounts)`

### 5 Whys
| # | Why? | Because… | Evidence (`file:line`) |
|---|------|----------|------------------------|
| 1 | Why does `average` crash on empty input? | It computes `sum(amounts) / len(amounts)`; with `amounts == []`, `len(amounts)` is `0`, so the division raises `ZeroDivisionError`. | `src/paycli/transactions.py:23` |
| 2 | Why is `len(amounts)` zero at runtime? | The CLI accepts zero-or-more amounts (`nargs="*"`), so the empty list is a permitted, reachable input. | `src/paycli/cli.py:19`, routed at `cli.py:34` |
| 3 | Why does the function divide without checking the count? | It assumes a non-empty sequence — the empty case was treated as out of scope and left unguarded. | `src/paycli/transactions.py:17-23` (no guard) |
| 4 | Why was the empty case assumed out of scope? | The function's implicit domain (`len ≥ 1`) was never reconciled with its actual public contract, which the `nargs="*"` argument widens to include `[]`. | mismatch between `src/paycli/transactions.py:23` and `src/paycli/cli.py:19` |
| 5 | Why was the contract mismatch never caught? | There is no test exercising `average_transaction([])`, so the undefined empty-domain behaviour produced no failing signal. | (absence) verified-research.md §2 cites only the routing, no empty-input test |

**Root Cause Statement:** The function's implicit precondition (a non-empty sequence) is **broader
in the caller than in the implementation**: `nargs="*"` admits `[]`, but the body divides by
`len(amounts)` unconditionally. The fundamental cause is an unhandled empty-domain edge case — a
contract/precondition gap between the CLI grammar and the function body. (`transactions.py:23` ×
`cli.py:19`)

---

## 4. VULN-1 — Command injection via `shell=True` f-string

### Symptom Analysis
- **Severity:** Critical. Arbitrary command execution: a crafted `path` (e.g. `x; rm -rf .`) runs
  attacker commands with the process's privileges.
- **Impact:** Full shell command injection through the `export` path argument — data loss, RCE,
  privilege-bounded system compromise.

### Fault Localization
- **Entry point:** `export` subcommand → `src/paycli/cli.py:38`
  `return export_report(args.path)`
- **Execution path:** `cli.main` → `export_report(path)` → `subprocess.call(..., shell=True)`
- **Fault point:** `src/paycli/report.py:21` — `return subprocess.call(f"cat {path} > report.txt", shell=True)`

### 5 Whys
| # | Why? | Because… | Evidence (`file:line`) |
|---|------|----------|------------------------|
| 1 | Why can `export` execute arbitrary commands? | `path` is interpolated into a command string run with `shell=True`, so shell metacharacters in `path` are interpreted as commands. | `src/paycli/report.py:21` |
| 2 | Why is a shell interpreting the input at all? | The call passes a single f-string with `shell=True` instead of an argument vector, delegating parsing to `/bin/sh`. | `src/paycli/report.py:21` |
| 3 | Why is caller input placed into that shell string unfiltered? | `path` is treated as trusted data and concatenated directly; it crosses from data into executable command text with no validation or escaping. | `src/paycli/report.py:15,21` |
| 4 | Why is `path` treated as trusted? | The argument is accepted raw at the CLI with no validation or sanitisation before reaching the shell. | `src/paycli/cli.py:27`, routed at `cli.py:38` |
| 5 | Why was no safe execution pattern chosen? | A convenience shell idiom (`cat ... > report.txt`) was used in place of a no-shell file-copy / argument-list approach; the design never separated the (trusted) command from the (untrusted) argument. | `src/paycli/report.py:21` (uses `shell=True` rather than `subprocess` arg list / Python file I/O) |

**Root Cause Statement:** Untrusted caller input is composed into a **shell-interpreted command
string** (`shell=True`), erasing the boundary between code and data. The fundamental cause is a
design choice to invoke a shell for a file operation while treating the path as trusted, so no
layer (CLI or function) ever separates command from argument or validates the input.
(`report.py:21` ← `cli.py:27`)

---

## 5. VULN-2 — Hardcoded secret in source

### Symptom Analysis
- **Severity:** High. A live-looking API credential is committed in source and shared with anyone
  who can read the repository or its history.
- **Impact:** Secret exposure; the credential cannot be rotated without a code change and persists
  in version-control history.

### Fault Localization
- **Entry point:** module import of `src/paycli/report.py` (module-scope assignment).
- **Execution path:** `import paycli.report` binds the literal at module load.
- **Fault point:** `src/paycli/report.py:12` — `API_KEY = "sk-live-DEMO0000000000000000000000"`

### 5 Whys
| # | Why? | Because… | Evidence (`file:line`) |
|---|------|----------|------------------------|
| 1 | Why is a secret exposed in the repository? | The API key is assigned as a string literal at module scope. | `src/paycli/report.py:12` |
| 2 | Why is the secret a source literal? | The value is hardcoded directly in code rather than read from an external source at runtime. | `src/paycli/report.py:12` |
| 3 | Why is it not read from an external source? | There is no configuration/secret-injection seam (e.g. `os.environ` lookup) in the module; the only place the value lives is the literal. | `src/paycli/report.py:9,12` (only `import subprocess`; no `os`/config import) |
| 4 | Why does no injection seam exist? | The module's design binds the credential's lifecycle to the code instead of to the deployment environment — secret management was never separated from source. | `src/paycli/report.py:1-12` |
| 5 | Why was secret management never separated? | No secret-handling policy/check gates the code (the literal pattern `sk-live-...` survives into the committed file), so embedding the value had no blocking signal. | `src/paycli/report.py:12`; CLAUDE.md "No secrets in committed code" (policy exists, not yet enforced in code) |

**Root Cause Statement:** The credential is **bound to the source artifact** rather than injected
from the environment, because the module provides no configuration seam to read it at runtime. The
fundamental cause is a missing separation between secret lifecycle and code lifecycle.
(`report.py:12`)

---

## 6. Risks (regression / edge cases)

- **BUG-A (`<` → `<=`):** Verify the *other* boundary is unaffected — strictly-over spends
  (`spent + amount > limit`) must still return `False`; only the exact-equal case changes.
  Watch float-equality at the boundary (`0.1 + 0.2` style) — the fix changes the endpoint, not the
  comparison's float semantics. (`transactions.py:32`)
- **BUG-B (empty guard):** Decide the empty-input return value deliberately (contract: `0`/`0.0`
  per docstring intent at `transactions.py:20-21`). Ensure a single-element list still averages
  correctly and that the guard does not alter the non-empty path. (`transactions.py:23`)
- **VULN-1 (no-shell rewrite):** A safe rewrite must preserve the observable contract — return an
  `int`-like status consumed by `cli.py:38` (`return export_report(...)`). Confirm behaviour for
  missing/unreadable `path` and that `report.txt` is still produced; avoid reintroducing a shell.
  (`report.py:21` → `cli.py:38`)
- **VULN-2 (env var):** Removing the literal must not break import-time behaviour; if the env var
  is absent, choose fail-fast vs. default deliberately. No current caller reads `API_KEY` in the
  verified call paths, so the regression surface is import-time only. (`report.py:12`)
- **Cross-cutting:** All four are independent (two in `transactions.py`, two in `report.py`); no
  shared state, so fixes can be planned in isolation. No fix touches `total()` (`transactions.py:14`).

---

## 7. References (`file:line` used)

- `src/paycli/transactions.py:14` — `total` (unaffected, scope boundary)
- `src/paycli/transactions.py:17-23` — `average_transaction` body (BUG-B)
- `src/paycli/transactions.py:23` — BUG-B fault line
- `src/paycli/transactions.py:26-32` — `is_within_daily_limit` body/docstring (BUG-A)
- `src/paycli/transactions.py:32` — BUG-A fault line
- `src/paycli/report.py:9` — `import subprocess`
- `src/paycli/report.py:12` — VULN-2 fault line
- `src/paycli/report.py:15,21` — `export_report` body / VULN-1 fault line
- `src/paycli/cli.py:19` — `average` `nargs="*"` (BUG-B contract widener)
- `src/paycli/cli.py:27` — `export` raw `path` (VULN-1 input)
- `src/paycli/cli.py:34` — routes `average`
- `src/paycli/cli.py:36` — routes `check-limit`
- `src/paycli/cli.py:38` — routes `export`
- `context/bugs/001/research/verified-research.md` — verified facts (source of analysis)

---

## Handoff → rca-verifier

RCA complete for all four verified issues; each has a ≥5-step 5 Whys chain ending in a
fundamental (specification / contract / design / lifecycle) cause, with `file:line` evidence on
every step. No code modified — analysis only. Please verify:

- **BUG-A** — `src/paycli/transactions.py:32` — root cause: exclusive `<` encodes an unspecified
  inclusive boundary; intended `<=`. Confirm 5 Whys depth and the boundary-test absence claim.
- **BUG-B** — `src/paycli/transactions.py:23` (× `cli.py:19`) — root cause: precondition gap, body
  assumes `len ≥ 1` while `nargs="*"` admits `[]`. Confirm the contract-mismatch reasoning.
- **VULN-1** — `src/paycli/report.py:21` (← `cli.py:27/38`) — root cause: untrusted input composed
  into a `shell=True` command string; code/data boundary erased. Confirm severity (Critical) and
  the trust-boundary chain.
- **VULN-2** — `src/paycli/report.py:12` — root cause: secret bound to source; no config seam.
  Confirm no runtime caller depends on the literal in verified call paths.

Open the cited `file:line`s and validate each chain reaches a fundamental cause (not a symptom);
flag any step lacking evidence or stopping at a shallow why. On PASS → CHECKPOINT 1 (human review)
→ bug-planner.
