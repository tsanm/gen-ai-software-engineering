"""Generic string-redaction helpers."""
from __future__ import annotations


def mask_account(account: str | None) -> str | None:
    """Redact an account identifier for logs/audit, keeping just enough to correlate.

    `ACC-12345` -> `ACC-1****`. Returns None unchanged.
    """
    if not account:
        return account
    if len(account) <= 5:
        return account[0] + "*" * (len(account) - 1)
    return account[:5] + "*" * (len(account) - 5)
