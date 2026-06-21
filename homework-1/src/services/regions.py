"""Region registry -- the single extension point for multi-country support (domain logic).

A `Region` bundles the things that differ by jurisdiction: default currency, the set of
allowed currencies, and the account-number format. Onboarding a new country = adding one
`Region` entry (and, if needed, an account-validator) -- no changes to routes or services.

Out of homework scope but seam-ready: real IBAN/routing validation, FX conversion
(see `RateProvider`), data-residency and retention policy could all hang off `Region`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

# Default homework account format: ACC- followed by exactly 5 alphanumerics.
DEFAULT_ACCOUNT_RE = re.compile(r"^ACC-[A-Za-z0-9]{5}$")


@dataclass(frozen=True)
class Region:
    code: str
    default_currency: str
    account_pattern: re.Pattern
    allowed_currencies: frozenset[str] | None = None  # None => any valid ISO 4217 code

    def is_valid_account(self, value: str) -> bool:
        return isinstance(value, str) and bool(self.account_pattern.match(value))


REGIONS: dict[str, Region] = {
    "DEFAULT": Region("DEFAULT", "USD", DEFAULT_ACCOUNT_RE),
    "US": Region("US", "USD", DEFAULT_ACCOUNT_RE),
    "EU": Region("EU", "EUR", DEFAULT_ACCOUNT_RE),
    "JP": Region("JP", "JPY", DEFAULT_ACCOUNT_RE),
}


def get_region(code: str) -> Region:
    return REGIONS.get(code, REGIONS["DEFAULT"])


# --- FX seam (documented, intentionally minimal for homework scope) --------

class RateProvider(Protocol):
    def convert(self, amount: Decimal, from_ccy: str, to_ccy: str) -> Decimal: ...


class IdentityRateProvider:
    """Placeholder FX provider. Same-currency only; cross-currency is a future extension."""

    def convert(self, amount: Decimal, from_ccy: str, to_ccy: str) -> Decimal:
        if from_ccy != to_ccy:
            raise NotImplementedError("Cross-currency conversion is not enabled in this build")
        return amount
