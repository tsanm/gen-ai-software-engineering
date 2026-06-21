# RCA Verifier — Decision Log (batch 001)

| step | decision | reason | evidence |
|------|----------|--------|----------|
| Load inputs | proceed | Read `rca.md` (4 chains) + `verified-research.md` (Quality: Verified) | rca.md:1-143; verified-research.md:11 |
| Re-confirm source | independent check | Don't trust upstream; re-read cited lines in source | transactions.py:23,27,32; report.py:9,12,21; cli.py:19,27,36,38 |
| BUG-A soundness | PASS | Each Why caused by next; Why4/5 split impl-mismatch vs missing spec/test; no leaps | rca.md:21-39 |
| BUG-A evidence | PASS | `<` confirmed; "within" contract confirmed; `100<100→False` correct | transactions.py:32, :27, :29-30 |
| BUG-B soundness | PASS | Crash→len 0→reachable input→no guard→no contract→no test; reachability proven not assumed | rca.md:49-67 |
| BUG-B evidence | PASS | Division confirmed; `nargs="*"` confirmed; seed comment corroborates | transactions.py:23, :20-21; cli.py:19 |
| VULN-1 soundness | PASS | exec→interpolation→untrusted flow→unneeded shell→no control; Why4/5 distinct roots | rca.md:77-97 |
| VULN-1 evidence | PASS | `shell=True` f-string + `import subprocess` confirmed; untrusted path flow confirmed | report.py:21, :9; cli.py:27, :38 |
| VULN-2 soundness | PASS | literal→inline→no lookup→config not separated→no policy; clean artifact→control chain | rca.md:107-124 |
| VULN-2 evidence | PASS | Literal confirmed; "no external lookup" verified — module imports only `subprocess`, no `os`/config | report.py:12, :7-9 |
| Overall verdict | PASS 4/4 | All chains sound + evidence-backed + actionable root causes; no gate triggered | this run |
| Gate | open | No chain failed; pipeline may proceed to CHECKPOINT 1 | overall verdict |
| Handoff | bug-planner | All 4 validated root causes forwarded, each pinned to confirmed line | result §Handoff |
