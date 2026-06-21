---
description: Validate all sample transactions without running the full pipeline.
---

Validate all transactions in `sample-transactions.json` without processing them.

Steps:
1. Run the validator in dry-run mode:
   `cd homework-6 && .venv/bin/python agents/transaction_validator.py --dry-run`
   (fall back to `python3 agents/transaction_validator.py --dry-run`).
2. Report: total count, valid count, invalid count, and the reason for each
   rejection.
3. Show the results as a table (transaction id, status, reason).

Do **not** run fraud detection, compliance, settlement, or reporting — this is
a fast pre-flight check of structural validity, currency (ISO 4217) and amount
rules only.
