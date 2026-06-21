#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block ``git push`` when coverage < 80%.

The hook receives the tool invocation as JSON on stdin. If the Bash command
being run is a ``git push``, this script runs the coverage gate and, if it
fails, returns a *deny* permission decision so the push never executes.

Exit codes / output follow the Claude Code hook protocol:
* a JSON object on stdout with ``hookSpecificOutput.permissionDecision`` set to
  ``"deny"`` (with a reason) blocks the tool call;
* ``"allow"`` lets it proceed.

For any non-push command the hook stays silent and allows the action.
"""

from __future__ import annotations

import json
import subprocess  # noqa: S404 - we run a fixed, local script only
import sys
from pathlib import Path

THRESHOLD = 80
GATE = Path(__file__).resolve().parent / "coverage_gate.sh"


def _decision(decision: str, reason: str) -> None:
    """Emit a PreToolUse permission decision and exit."""

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # not a hook invocation we understand; do nothing

    tool = payload.get("tool_name", "")
    command = str(payload.get("tool_input", {}).get("command", ""))

    if tool != "Bash" or "git push" not in command:
        sys.exit(0)  # only gate pushes

    result = subprocess.run(  # noqa: S603 - fixed local script, no shell injection
        ["bash", str(GATE), str(THRESHOLD)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        _decision(
            "deny",
            f"Coverage gate failed (threshold {THRESHOLD}%). Push blocked.\n"
            + result.stdout[-1500:]
            + result.stderr[-500:],
        )
    _decision("allow", f"Coverage gate passed (>= {THRESHOLD}%).")


if __name__ == "__main__":
    main()
