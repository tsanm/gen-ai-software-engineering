"""Application settings.

Settings are immutable and injected into the app factory (`create_app`). This keeps
the app testable (each test builds its own settings) and avoids hidden global config.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Settings:
    region: str = "DEFAULT"
    rate_limit_max: int = 100
    rate_limit_window_seconds: int = 60
    large_amount_threshold: Decimal = Decimal("10000")
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables (used for real `uvicorn` runs)."""
        return cls(
            region=os.getenv("REGION", "DEFAULT"),
            rate_limit_max=int(os.getenv("RATE_LIMIT_MAX", "100")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            large_amount_threshold=Decimal(os.getenv("LARGE_AMOUNT_THRESHOLD", "10000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
