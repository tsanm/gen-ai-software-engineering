# RCA Analyst Result — paycli (batch 001)

Architect mode (read-only). Derives the root cause of each **Verified** issue from
`context/bugs/001/verified-research.md` using the **5 Whys** technique. No code was edited
and no fixes are proposed — root cause only.

Each chain is grounded in source confirmed at the cited `file:line`:
- `src/paycli/transactions.py:32` — `return spent + amount < limit`
- `src/paycli/transactions.py:23` — `return sum(amounts) / len(amounts)`
- `src/paycli/report.py:21` — `return subprocess.call(f"cat {path} > report.txt", shell=True)`
- `src/paycli/report.py:12` — `API_KEY = "sk-live-DEMO0000000000000000000000"`

---

## BUG-A — boundary off-by-one in daily-limit check
**File:** `src/paycli/transactions.py:32` (reached via `cli.py:36`, `check-limit` command)

**Symptom:** A spend that lands *exactly* on the daily limit (`spent + amount == limit`)
is reported as **not** within the limit; `check-limit 60 40 100` returns `False`.

- **Why 1 — Why is an exact-limit spend rejected?**
  The function returns `spent + amount < limit`; a strict `<` evaluates `100 < 100` as
  `False`, excluding the boundary value. (`transactions.py:32`)
- **Why 2 — Why is a strict `<` used?**
  The comparison operator was chosen as `<` when the function's contract — "keeps the
  day's total *within* `limit`" (`transactions.py:27`) — requires the inclusive `<=`.
- **Why 3 — Why does the operator not match the contract?**
  The inclusive-upper-bound semantics ("on the limit is allowed") were never translated
  into the comparison; the boundary case was not reasoned about when the line was written.
- **Why 4 — Why was the mismatch not caught?**
  No boundary-value test exercises the `spent + amount == limit` case, so the off-by-one
  produces no failing signal.
- **Why 5 — Why is there no such test/spec?**
  "Exactly on the limit is permitted" was never recorded as an explicit acceptance
  criterion, so neither the implementation nor the test suite was anchored to it.

**Root Cause:** An **inclusive** upper-bound business rule ("a spend equal to the limit is
allowed") was implemented with an **exclusive** operator (`<` instead of `<=`) and was
never pinned by a boundary test, so equality with the limit is silently rejected.

---

## BUG-B — unguarded division by zero in average
**File:** `src/paycli/transactions.py:23` (reached via `cli.py:34`, `average` command)

**Symptom:** Averaging an empty list raises `ZeroDivisionError` instead of returning a
defined value; `paycli average` (no amounts) crashes.

- **Why 1 — Why does it crash on empty input?**
  It computes `sum(amounts) / len(amounts)`; for an empty sequence `len(amounts)` is `0`,
  so the division raises `ZeroDivisionError`. (`transactions.py:23`)
- **Why 2 — Why is `len(amounts)` zero at runtime?**
  An empty sequence is a reachable input: the CLI declares `amounts` with `nargs="*"`
  (`cli.py:19`), so passing no values yields an empty list straight into the function.
- **Why 3 — Why does the function not handle the empty case?**
  It assumes a non-empty sequence; there is no guard (e.g. `if not amounts: return 0`)
  before dividing.
- **Why 4 — Why is the empty case unhandled?**
  The function's contract never defines a return value for empty input — the docstring
  describes only the average, leaving the empty-sequence behavior undefined.
- **Why 5 — Why was the undefined behavior never surfaced?**
  No test exercises the empty-sequence path, so the missing edge-case handling is invisible
  until a user triggers it.

**Root Cause:** `average_transaction` has an **unhandled edge case** — it assumes a
non-empty sequence and lacks a guard for empty input, even though a reachable caller (the
CLI's `nargs="*"`) can pass an empty list, and no contract or test defines the empty result.

---

## VULN-1 — command injection via shell=True
**File:** `src/paycli/report.py:21` (path flows from `cli.py:27` → `cli.py:38`; `import subprocess` at `report.py:9`)

**Symptom:** A crafted `path` (e.g. `export "x; rm -rf ."`) executes arbitrary shell
commands on the host.

- **Why 1 — Why can arbitrary commands run?**
  `export_report` runs `subprocess.call(f"cat {path} > report.txt", shell=True)`; with
  `shell=True` the constructed string is interpreted by a shell. (`report.py:21`)
- **Why 2 — Why does attacker input reach the shell?**
  `path` is interpolated directly into the command string with no quoting, escaping, or
  validation — caller-supplied data is concatenated into executable text.
- **Why 3 — Why is the caller input untrusted yet trusted?**
  `path` originates from an external CLI argument (`cli.py:27` → `cli.py:38`) but is
  treated as if it were safe command text; no trust boundary is enforced on it.
- **Why 4 — Why is a shell used at all?**
  A shell was invoked to perform a simple file concatenation/copy that Python file I/O
  (or `subprocess` with an argument list, no shell) could do without an interpreter —
  the wrong, more powerful tool was chosen for the task.
- **Why 5 — Why was the dangerous construction chosen?**
  String-built `shell=True` commands were used without applying the secure-by-default
  practice (pass args as a list / avoid the shell), and no review or check flagged
  untrusted interpolation into a shell.

**Root Cause:** `export_report` builds a **shell command from untrusted caller input** and
executes it with `shell=True`, with no argument list, quoting, or validation — and uses a
shell where none is needed — collapsing the trust boundary and enabling command injection.

---

## VULN-2 — hardcoded secret in source
**File:** `src/paycli/report.py:12`

**Symptom:** A live-looking credential (`API_KEY = "sk-live-DEMO0000000000000000000000"`)
is committed in plaintext in the repository.

- **Why 1 — Why is a secret exposed?**
  `API_KEY` is assigned a string literal directly in module-level source. (`report.py:12`)
- **Why 2 — Why is the value in the literal?**
  The credential was embedded inline in code rather than supplied from outside the source
  tree at runtime.
- **Why 3 — Why is it supplied inline?**
  The module reads no external configuration — there is no `os.environ` / config-file /
  secret-store lookup to source the value from.
- **Why 4 — Why is there no external lookup?**
  Configuration is not separated from code; the inline literal was the path of least
  resistance with no convention for loading credentials.
- **Why 5 — Why did the inline secret persist?**
  No policy or automated control (secret scanning, config convention, review gate)
  prevents committing credentials to source, so it went unflagged.

**Root Cause:** The credential is **stored in source instead of being injected from the
environment / a secret store**, because no configuration boundary separates secrets from
code and no control prevents committing them.

---

## Handoff -> rca-verifier
Four root causes derived, one per Verified issue, each ending in an actionable Root Cause
and grounded in confirmed source lines:

1. **BUG-A** (`transactions.py:32`) — inclusive limit rule implemented with exclusive `<`;
   should be `<=`, unpinned by any boundary test.
2. **BUG-B** (`transactions.py:23`) — unhandled empty-sequence edge case; no guard before
   dividing by `len`, reachable via CLI `nargs="*"`.
3. **VULN-1** (`report.py:21`) — untrusted input interpolated into a `shell=True` command;
   broken trust boundary + unnecessary shell.
4. **VULN-2** (`report.py:12`) — secret stored in source rather than injected from
   environment/secret store; missing config boundary.

Validate each 5-Whys chain for logical soundness (each Why causes the one above) and that
every claim ties to the cited evidence. No fixes proposed — that is the planner's job.
