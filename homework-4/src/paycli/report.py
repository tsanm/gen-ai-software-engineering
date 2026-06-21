"""Report export for paycli.

NOTE: this module contains intentional seeded security issues for the pipeline to
find (see context/bugs/001/bug-context.md). The values/paths are demo-only.
"""

from __future__ import annotations

import os
import shutil

# Credential is injected from the environment; no secret is committed in source.
API_KEY = os.environ.get("PAYCLI_API_KEY", "")


def export_report(path: str) -> int:
    """Copy the file at ``path`` into ``report.txt``.

    ``path`` is treated strictly as data: the copy uses a no-shell library call,
    so shell metacharacters in ``path`` cannot be interpreted as commands.
    Returns 0 on success and 1 if the source cannot be read.
    """
    try:
        shutil.copyfile(path, "report.txt")
    except OSError:
        return 1
    return 0
