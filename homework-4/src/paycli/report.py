"""Report export for paycli.

NOTE: this module contains intentional seeded security issues for the pipeline to
find (see context/bugs/001/bug-context.md). The values/paths are demo-only.
"""

from __future__ import annotations

import subprocess

# VULN-2: hardcoded secret committed in source (fake value, for the security agent to flag).
API_KEY = "sk-live-DEMO0000000000000000000000"


def export_report(path: str) -> int:
    """Concatenate the file at ``path`` into ``report.txt``.

    VULN-1: builds a shell command from caller-supplied input with ``shell=True``,
    enabling command injection (e.g. ``path = "x; rm -rf ."``).
    """
    return subprocess.call(f"cat {path} > report.txt", shell=True)
