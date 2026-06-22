---
description: Generate a project specification from the banking-pipeline template.
argument-hint: "[feature or project name]"
---

# Agent 1 — Write the Specification

You are **Agent 1 (Specification)**. Produce a complete technical specification
for: **$ARGUMENTS** (default to "the multi-agent banking transaction pipeline"
if no argument is given), writing it to `homework-6/specification.md`.

Follow this exact template and fill every section with concrete, testable
content (no placeholders):

```markdown
# <Feature Name> Specification

> Ingest the information from this file, implement the Low-Level Tasks, and
> generate the code that will satisfy the High and Mid-Level Objectives.

## 1. High-Level Objective
- <one clear sentence describing what the pipeline does>

## 2. Mid-Level Objectives (4-5)
- <concrete, testable requirement>
- ...

## 3. Implementation Notes
- Monetary values: use `decimal.Decimal` (never `float`)
- Currency codes: ISO 4217 (USD, EUR, GBP, JPY, ...)
- Logging: audit trail with ISO-8601 timestamp, agent name, transaction id, outcome
- PII: treat account numbers and names as sensitive — no plaintext logging

## 4. Context
### Beginning context
- `sample-transactions.json` with raw transaction records
### Ending context
- processed results in `shared/results/`, a pipeline summary, coverage >= 90%

## 5. Low-Level Tasks (one per agent)
Each entry MUST use this format:

Task: <Agent Name>
Prompt: "<exact prompt you would give Claude Code>"
File to CREATE: agents/<agent_name>.py
Function to CREATE: process_message(message: dict) -> dict
Details: <what the agent checks / transforms / decides>
```

## Steps
1. Read `homework-6/sample-transactions.json` first so the spec reflects the
   real input shape. **Output:** a fields table `field · type · example`.
2. Write the High-Level Objective + 4–5 Mid-Level Objectives.
   **Output:** the objectives block.
3. Write the Implementation Notes verbatim — they encode the engineering
   invariants (Decimal money, ISO-4217, audit logging, no plaintext PII).
   **Output:** the notes block.
4. Write the Context and a Low-Level Task for **every** agent in the pipeline
   (validator, fraud detector, compliance checker, settlement processor,
   reporting agent). **Output:** one Low-Level Task block per agent.
5. Write `homework-6/specification.md` with the Authority note, the 5 sections,
   `## Assumptions`, and a `## Traceability` table. **Output:** the spec file.

## Expected output
`homework-6/specification.md` containing all 5 sections (no placeholders), an
Authority/closed-world note, `## Assumptions`, and a `## Traceability` table.

**Self-check:** print a checklist confirming all 5 sections + Assumptions +
Traceability are present and no field/threshold was invented beyond the input.
