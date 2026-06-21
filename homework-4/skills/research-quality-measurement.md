---
name: research-quality-measurement
description: Measure and label the quality of bug-research findings. Use when verifying a Bug Researcher's codebase-research so the verified-research report carries a consistent, explicit Research Quality level.
---

# Research Quality Measurement

Use this when writing `verified-research.md`. Assign **exactly one** Research Quality level.

## Levels
| Level | Criteria |
|-------|----------|
| **Verified** | 100% of claims have a resolving `file:line` and the quoted snippet matches source exactly; no discrepancies. |
| **Partially Verified** | ≥1 claim verified, but ≥1 discrepancy (wrong line, paraphrased snippet, or missing reference). |
| **Unverified** | Core claims cannot be confirmed against source, or discrepancies make the research unsafe to act on. |

## Required sections for `verified-research.md`
1. **Verification Summary** — overall pass/fail + the Research Quality level.
2. **Verified Claims** — table: claim · `file:line` · snippet-matches? (yes/no).
3. **Discrepancies Found** — list each, or state "None".
4. **Research Quality Assessment** — the level + ≥1 sentence of reasoning.
5. **References** — the source files inspected.

## Gate
If the level is **Unverified**, say so in the Verification Summary — the pipeline stops before planning.
