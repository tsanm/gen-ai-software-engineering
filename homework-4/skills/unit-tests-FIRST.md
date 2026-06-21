---
name: unit-tests-first
description: Apply the FIRST principles when generating unit tests. Use when creating tests for changed code so each test is Fast, Independent, Repeatable, Self-validating, and Timely.
---

# Unit Tests — FIRST

Apply to every generated test; record compliance in `test-report.md`.

## Principles
- **Fast** — runs in milliseconds; no network, sleep, or heavy I/O (whole suite < 5s).
- **Independent** — no shared mutable state or ordering dependency; passes in any order.
- **Repeatable** — deterministic; same result every run, any machine (use `tmp_path`, fixed inputs).
- **Self-validating** — asserts a precise expected value; pass/fail is automatic, no manual check.
- **Timely** — written with the change; covers exactly the changed code (boundaries + the fix).

## Checklist (tick per test in `test-report.md`)
- [ ] Targets changed code only (BUG-A boundary, BUG-B empty, VULN-1 injection-blocked)
- [ ] One behaviour per test, descriptive name
- [ ] Deterministic inputs; isolated side effects (`tmp_path`)
- [ ] Has ≥1 explicit `assert`
- [ ] Fast (no sleeps / network)
