"""Report export for paycli."""

from __future__ import annotations

import os
import shutil

# API key is read from the environment, never committed to source.
API_KEY = os.environ.get("PAYCLI_API_KEY", "")


def export_report(path: str) -> int:
    """Copy the file at ``path`` into ``report.txt`` using plain file I/O.

    No shell is involved, so a caller-supplied ``path`` cannot inject commands.
    Returns 0 on success and 1 if the source path cannot be read.
    """
    try:
        with open(path, "rb") as src, open("report.txt", "wb") as dst:
            shutil.copyfileobj(src, dst)
    except OSError:
        return 1
    return 0
