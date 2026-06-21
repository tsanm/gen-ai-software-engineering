# Stronger Proofs — Homework 4

Evidence the pipeline is real, correct, and robust. Raw captures alongside this file.

| # | Proof | What it shows | Result | Evidence |
|---|-------|---------------|--------|----------|
| **A** | End-to-end green | the whole pipeline runs and the gate holds | `verify.sh` **46/46 P0 pass** (excl. 4 author screenshots); coverage 100%; bandit clean | [`verify-output.txt`](verify-output.txt) |
| **B** | Surprise *undocumented* bug | the security-verifier genuinely analyses (doesn't echo the seed) | caught an unseeded `eval()` **RCE (CRITICAL)** + hardcoded secret (HIGH) + timing attack (MEDIUM) + 2 more, each with `file:line` + remediation; made **no edits** (read-only) | [`surprise-bug.txt`](surprise-bug.txt) |
| **C** | Human checkpoint gate | checkpoints are real gates, not no-ops | approve → continue (exit 0); reject → **stop (exit 3)** + decision recorded | [`checkpoint-gate.txt`](checkpoint-gate.txt) |
| **D** | Immutability | each run is captured independently; history is not mutated | a 2nd full run created a new timestamped folder; the 1st stayed **byte-identical** (hash `72123b07…`) | [`immutability.txt`](immutability.txt) |

Reproduce A: `./verify.sh`. The two live run folders are under `context/bugs/001/runs/`.
