"""Application settings.

Settings are immutable and injected into the app factory (`create_app`). This keeps
the app testable (each test builds its own settings) and avoids hidden global config.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Maximum number of records accepted in a single bulk import (a sane DoS guard).
    max_import_records: int = 1000
    # Maximum size (bytes) of an uploaded import file.
    max_import_bytes: int = 5_000_000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables (used for real `uvicorn` runs)."""
        return cls(
            max_import_records=int(os.getenv("MAX_IMPORT_RECORDS", "1000")),
            max_import_bytes=int(os.getenv("MAX_IMPORT_BYTES", "5000000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
