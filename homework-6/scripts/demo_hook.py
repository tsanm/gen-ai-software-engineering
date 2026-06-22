#!/usr/bin/env python3
"""Readable demonstration of the coverage-gate PreToolUse hook.

Invokes the *real* hook (``scripts/pre_push_hook.py``) against a simulated
``git push`` at two thresholds and renders the decisions cleanly:

* demo gate at 100% -> the hook returns **DENY** (coverage is ~99%);
* real gate at  80% -> the hook returns **ALLOW**.

Nothing is mocked -- the hook runs the real coverage gate each time, so the
coverage percentage shown is genuine.

Usage:  python scripts/demo_hook.py
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pre_push_hook as hook  # noqa: E402

PUSH = json.dumps(
    {"tool_name": "Bash", "tool_input": {"command": "git push origin atsiatsko_home_work_6"}}
)

# ANSI styling (kept simple so a screenshot is legible).
B, D, G, R, Y, X = "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def _decision(threshold: int) -> dict[str, str]:
    """Run the real hook at ``threshold`` and return its hookSpecificOutput."""

    original_threshold = hook.THRESHOLD
    original_stdin = sys.stdin
    captured = io.StringIO()
    hook.THRESHOLD = threshold
    sys.stdin = io.StringIO(PUSH)
    try:
        with contextlib.redirect_stdout(captured), contextlib.suppress(SystemExit):
            hook.main()
    finally:
        hook.THRESHOLD = original_threshold
        sys.stdin = original_stdin
    payload: dict[str, dict[str, str]] = json.loads(captured.getvalue())
    return payload["hookSpecificOutput"]


def main() -> None:
    blurb = "Intercepts every Bash `git push` and blocks it when coverage is below the gate."
    print(f"{B}PreToolUse hook — scripts/pre_push_hook.py{X}")
    print(f"{D}{blurb}{X}\n")
    print(f"  $ {B}git push origin atsiatsko_home_work_6{X}")
    print(f"  {D}↳ intercepted by hook → running coverage gate on the real test suite…{X}\n")

    deny = _decision(100)
    allow = _decision(80)

    pct_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", deny["permissionDecisionReason"])
    pct = int(pct_match.group(1)) if pct_match else 0
    print(f"  measured total coverage: {B}{pct}%{X}\n")

    d_ok = deny["permissionDecision"] == "deny"
    a_ok = allow["permissionDecision"] == "allow"
    print(
        f"  {R}✖ DENY{X}   demo gate {B}100%{X}   "
        f"{pct}% < 100%   → push {R}BLOCKED{X}   "
        f"{D}(decision={deny['permissionDecision']}){X}"
    )
    print(
        f"  {G}✔ ALLOW{X}  real gate  {B}80%{X}   "
        f"{pct}% ≥ 80%    → push {G}PERMITTED{X}   "
        f"{D}(decision={allow['permissionDecision']}){X}"
    )

    ok = d_ok and a_ok
    colour = G if ok else R
    print(f"\n  {colour}{'✔ hook behaves correctly' if ok else '✖ unexpected decision'}{X}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
