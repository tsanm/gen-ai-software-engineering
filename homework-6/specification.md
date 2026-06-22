# Multi-Agent Banking Transaction Pipeline — Specification

**Author:** Anton Tsiatsko
**Produced by:** Agent 1 (Specification) — generatable via `/write-spec`.

> Ingest the information from this file, implement the Low-Level Tasks, and
> generate the code that will satisfy the High and Mid-Level Objectives.

## Authority & sources of truth (read first)

This specification is the **single source of truth (SSOT)** for WHAT to build —
its objectives, thresholds, fee rate, currencies, fields and codes are
authoritative. `agents.md` defines HOW agents behave; `CLAUDE.md` is the
always-on subset of the rules. The four meta-agent definitions live in
`agents-meta/*.agent.md`.

**Closed-world rule:** do **not** invent endpoints, fields, currencies, or codes
that are not defined here or present in `sample-transactions.json`. If a needed
value is undefined, **ask — do not guess** (and, if a sensible default is chosen,
record it under `## Assumptions`). Unknown / malformed input ⇒ **fail closed**
(reject with a human-readable `reason`).

## 1. High-Level Objective

- Build a cooperating multi-agent pipeline that validates, risk-scores,
  compliance-screens, settles and reports on raw banking transactions read
  from `sample-transactions.json`, writing a terminal outcome per transaction
  into `shared/results/`.

## 2. Mid-Level Objectives (4–5, concrete and testable)

- **Validation:** every transaction is checked for required fields, a non-zero
  well-formed amount, and a supported ISO-4217 currency; invalid transactions
  are rejected with a human-readable `reason`.
- **Fraud scoring:** transactions are assigned an explainable `risk_score`
  (0–100) and `risk_band`; high-risk transactions (e.g. ≥ $50,000 or
  high-value wires) are flagged for review and never auto-settle.
- **Compliance:** transactions touching a blocked account are rejected;
  transactions ≥ 10,000 raise a `regulatory_report_required` flag; fraud-flagged
  transactions are held.
- **Settlement & reporting:** approved transactions settle with a `Decimal` fee
  and net amount (ROUND_HALF_UP); all rejected transactions are written to
  `shared/results/` with a reason; a run summary is produced.
- **Auditability:** every agent operation is logged with an ISO-8601 timestamp,
  agent name, transaction id and outcome — with no plaintext PII.

## 3. Implementation Notes

- Monetary values: use `decimal.Decimal` for **all** amounts — never `float`.
  Parse from strings; quantise with `ROUND_HALF_UP` to the currency's minor units.
- Currency codes: ISO 4217 (USD, EUR, GBP, JPY, CHF, CAD, AUD). Unknown codes
  (e.g. `XYZ`) are rejected.
- Logging: an audit trail line per operation = `timestamp agent txn outcome`
  (+ optional masked detail). Account numbers and descriptions are PII and are
  masked (`ACC-1001` → `****01`) before logging.
- Communication: agents exchange the standard JSON envelope via files in
  `shared/{input,processing,output,results}`.
- Testing: unit tests per agent + an integration test for the full pipeline,
  isolated from the real `shared/` via `tmp_path`. Target coverage ≥ 90%.
- Configuration: the runtime numbers (agent order, fraud/compliance thresholds,
  fee rate, currency allow-list, paths, coverage floor) live in
  `pipeline.config.json`; `integrator.py` and the agents **read** them, so tuning
  a threshold needs no code change. The values in that file mirror this spec.
- Run capture: each `integrator.py` run writes an immutable, timestamped folder
  under `shared/runs/run-<UTC>/` containing the per-transaction results, a
  PII-safe audit log, the run summary, and a `manifest.json`. `shared/results/`
  holds the latest run as a convenience pointer.

## 3a. Worked Example (one transaction, end to end)

This traces **TXN001** from the raw record through each agent to its terminal
result, so the expected behaviour is unambiguous.

**Raw input** (`sample-transactions.json`):

```json
{ "transaction_id": "TXN001", "timestamp": "2026-03-16T09:00:00Z",
  "source_account": "ACC-1001", "destination_account": "ACC-2001",
  "amount": "1500.00", "currency": "USD", "transaction_type": "transfer",
  "metadata": { "channel": "online", "country": "US" } }
```

**Message envelope** the integrator seeds into `shared/input/` (standard wire
format):

```json
{ "message_id": "<uuid4>", "timestamp": "<iso-8601>",
  "source_agent": "integrator", "target_agent": "transaction_validator",
  "message_type": "transaction", "data": { ...the raw record... } }
```

**Per-agent decisions:**

| Stage | Decision | Key fields added | Next target |
|---|---|---|---|
| `transaction_validator` | all 7 required fields present; USD supported; amount `1500.00` non-zero → **validated** (amount normalised to `1500.00`) | `status=validated` | `fraud_detector` |
| `fraud_detector` | amount < 5,000 (0 pts); 09:00 UTC not off-hours (0); country `US` domestic (0); not a wire (0) → score `0` | `risk_score=0`, `risk_band=low`, `status=passed_fraud` | `compliance_checker` |
| `compliance_checker` | neither account blocked; amount < 10,000 → no report flag; not fraud-flagged → **approved** | `compliance_decision=approved`, `compliance_flags=[]`, `status=compliance_approved` | `settlement_processor` |
| `settlement_processor` | fee = `1500.00 × 0.0025` = `3.75`; net = `1500.00 − 3.75` = `1496.25` (Decimal, ROUND_HALF_UP) | `fee=3.75`, `net_amount=1496.25`, `status=settled` | `reporting_agent` |
| `reporting_agent` | finalise + stamp | `finalized_at`, written to `shared/results/TXN001.json` | terminal |

**Terminal result** (`shared/results/TXN001.json` → `data`): `status=settled`,
`fee=3.75`, `net_amount=1496.25`. Each hop emits one PII-safe audit line
(`<iso-8601> agent=<name> txn=TXN001 outcome=<status> detail=src=****01`).

## 3b. Outcome & Reason Catalog (authoritative)

Every transaction reaches exactly one **terminal status**; rejected/held records
carry a stable, human-readable `reason`. This catalog is the single source of
truth for those codes — agents must not invent statuses or reasons outside it.

| Terminal `status` | Meaning | Set by | Settles? |
|---|---|---|---|
| `settled` | Approved and money math applied (`fee`, `net_amount`) | settlement_processor | yes |
| `held` | Fraud-flagged; never auto-settles, awaits manual review | compliance_checker | no |
| `rejected` | Failed validation or compliance; terminal with a `reason` | validator / compliance | no |

| Reason code (`reason`) | When it occurs | Originating agent |
|---|---|---|
| `missing required field: <name>` | A required field is absent/empty | transaction_validator |
| `unsupported currency: <code>` | Currency not in the ISO-4217 allow-list (e.g. `XYZ`) | transaction_validator |
| `amount must be non-zero` | Parsed amount equals zero | transaction_validator |
| `negative amount only allowed for refunds` | Negative amount on a non-refund type | transaction_validator |
| `invalid monetary amount: <value>` | Amount is a `float` or unparseable | transaction_validator |
| `blocked_account` | Source/destination is on the compliance blocklist | compliance_checker |
| `fraud_review` | Risk score ≥ review threshold → held (this is a hold reason, not a rejection) | compliance_checker |

**Non-terminal status flags** (set mid-chain, never persisted as a terminal
outcome): `validated`, `passed_fraud`, `compliance_approved`. **Compliance flag:**
`regulatory_report_required` is raised (in `compliance_flags`) at amount ≥ the
reporting threshold; it annotates but does not by itself change the outcome.

## 4. Context

### Beginning context
- `sample-transactions.json` — raw transaction records (8 sample rows).
- Empty `shared/` message-bus directories.

### Ending context
- `shared/results/<TXN>.json` — one terminal envelope per transaction.
- `shared/results/_summary.{json,txt}` — pipeline run summary report.
- Test coverage ≥ 90%; quality gate (ruff/mypy/bandit/radon) clean.

## 5. Low-Level Tasks (one per agent)

```
Task: Transaction Validator
Prompt: "Create the transaction validator agent. It must check all required
         fields, reject zero/invalid amounts (allowing negative only for
         refunds), and reject unsupported ISO-4217 currencies. Normalise the
         amount to the currency's minor units. Expose process_message and a
         --dry-run CLI."
File to CREATE: agents/transaction_validator.py
Function to CREATE: process_message(message: dict) -> dict
Details: Validates structure, amount and currency; routes valid -> fraud_detector,
         rejected -> reporting_agent. Never logs raw account numbers.
```

```
Task: Fraud Detector
Prompt: "Create the fraud detector agent. Compute an explainable weighted risk
         score from high-value bands, off-hours timing (00:00-05:00 UTC),
         cross-border country and wire-transfer rail. Cap at 100; flag >= 50
         for review."
File to CREATE: agents/fraud_detector.py
Function to CREATE: process_message(message: dict) -> dict
Details: Adds risk_score, risk_band, risk_reasons; routes to compliance_checker.
```

```
Task: Compliance Checker
Prompt: "Create the compliance checker agent. Reject transactions to/from a
         blocked-account list, raise a regulatory_report_required flag at
         >= 10,000, and hold transactions flagged for fraud review."
File to CREATE: agents/compliance_checker.py
Function to CREATE: process_message(message: dict) -> dict
Details: Sets compliance_decision and compliance_flags; routes to settlement_processor.
```

```
Task: Settlement Processor
Prompt: "Create the settlement processor agent. For compliance-approved
         transactions compute a 0.25% fee and net amount using Decimal with
         ROUND_HALF_UP; pass held/rejected transactions through unchanged."
File to CREATE: agents/settlement_processor.py
Function to CREATE: process_message(message: dict) -> dict
Details: Adds fee, net_amount, settlement_status=settled; routes to reporting_agent.
```

```
Task: Reporting Agent
Prompt: "Create the reporting agent. Finalise each record into shared/results/
         and build a run summary: counts by status, settled totals per
         currency, flagged-for-review list, rejected list with reasons."
File to CREATE: agents/reporting_agent.py
Function to CREATE: process_message(message: dict) -> dict
Details: Terminal agent; also exposes build_summary / render_summary_text /
         write_summary used by the integrator and the MCP summary resource.
```

```
Task: Integrator / Orchestrator
Prompt: "Create the integrator. Set up shared/ directories, load
         sample-transactions.json, seed input envelopes, run the agent chain in
         order with short-circuiting for terminal statuses, persist results and
         confirm every transaction was processed."
File to CREATE: integrator.py
Function to CREATE: run_pipeline(sample_path, shared_root, logger) -> dict
Details: Drives the file-based protocol; returns a summary with all_processed/missing.
```

## Assumptions

These hold unless the requirements say otherwise; each is a deliberate default,
not an invented requirement (see the closed-world rule above).

- **Supported currencies** are exactly USD, EUR, GBP, JPY, CHF, CAD, AUD; any
  other ISO-4217 (or non-ISO) code is rejected.
- **Negative amounts** are valid **only** for refunds; all other types require a
  positive, non-zero amount.
- **Off-hours** for fraud scoring means 00:00–05:00 UTC; timestamps are ISO-8601
  and interpreted as UTC.
- **Regulatory reporting** is flagged at amount ≥ 10,000 (transaction currency
  units); the high-value fraud band starts at $50,000-equivalent.
- **Settlement fee** is a flat 0.25% of the amount, quantised `ROUND_HALF_UP` to
  the currency's minor units; held/rejected transactions are passed through
  unchanged.
- **Account numbers and descriptions are PII** and are masked before any log line
  or MCP response (`ACC-1001` → `****01`).
- The pipeline is **single-run, batch** over `sample-transactions.json`; the
  file-based bus is not concurrent across processes.
- **Coverage gate floor is 80%** (push-blocking); the suite targets ≥ 90%.

## Traceability

Each meta-agent (defined in `agents-meta/`) produces specific deliverables,
verified by specific tests.

| Meta-agent (`agents-meta/`) | Deliverable file(s) | Test file(s) |
|---|---|---|
| `spec-agent.agent.md` (Spec) | `specification.md`, `agents.md`, `CLAUDE.md`, `.claude/commands/write-spec.md` | n/a (verified by `verify.sh` content checks) |
| `code-agent.agent.md` (Code) | `integrator.py`, `agents/*.py`, `mcp/server.py`, `research-notes.md` | `tests/test_integration.py`, `tests/test_integrator_cli.py`, `tests/test_mcp_server.py` |
| `test-agent.agent.md` (Tests) | `tests/`, coverage gate (`scripts/pre_push_hook.py`, `.claude/settings.json`) | `tests/test_common.py`, `tests/test_transaction_validator.py`, `tests/test_fraud_detector.py`, `tests/test_compliance_checker.py`, `tests/test_settlement_processor.py`, `tests/test_reporting_agent.py` |
| `doc-agent.agent.md` (Docs) | `README.md`, `HOWTORUN.md`, `docs/screenshots/` | n/a (verified by `verify.sh` content checks) |
