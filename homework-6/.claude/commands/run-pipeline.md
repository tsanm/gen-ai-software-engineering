---
description: Run the multi-agent banking pipeline end-to-end and summarise results.
---

Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that `homework-6/sample-transactions.json` exists; abort with a clear
   message if it does not.
2. Clear the `homework-6/shared/` directories (input, processing, output,
   results) so the run starts clean.
3. Run the pipeline: `cd homework-6 && .venv/bin/python integrator.py`
   (fall back to `python3 integrator.py` if no venv is present).
4. Show a summary of results from `homework-6/shared/results/`:
   - total transactions, and a count by final status (settled / held / rejected)
   - the settled totals per currency from `shared/results/_summary.txt`
5. Report any transactions that were rejected and **why**, and any flagged for
   fraud review with their risk score.

Finish by confirming that every transaction id from `sample-transactions.json`
appears in `shared/results/`.
