"""ISO 4217 currency reference data.

Each currency carries its number of *minor units* (decimal exponent). Amount precision
is validated against this table rather than a hardcoded "2 decimals", so the same engine
correctly handles JPY (0), USD/EUR/GBP (2) and BHD/KWD/OMR (3). Adding a currency for a
new region is a one-line table edit -- no code changes.
"""
from __future__ import annotations

from decimal import Decimal

# code -> minor units (decimal places). A representative ISO 4217 subset.
MINOR_UNITS: dict[str, int] = {
    # 2 decimals (most currencies)
    "USD": 2, "EUR": 2, "GBP": 2, "AUD": 2, "CAD": 2, "CHF": 2, "CNY": 2,
    "HKD": 2, "NZD": 2, "SGD": 2, "SEK": 2, "NOK": 2, "DKK": 2, "PLN": 2,
    "ZAR": 2, "INR": 2, "BRL": 2, "MXN": 2, "RUB": 2, "TRY": 2, "AED": 2,
    "SAR": 2, "THB": 2, "MYR": 2, "PHP": 2, "CZK": 2, "ILS": 2, "UAH": 2,
    # 0 decimals
    "JPY": 0, "KRW": 0, "CLP": 0, "VND": 0, "ISK": 0, "XOF": 0, "XAF": 0,
    # 3 decimals
    "BHD": 3, "KWD": 3, "OMR": 3, "JOD": 3, "TND": 3, "LYD": 3, "IQD": 3,
}

VALID_CURRENCIES = frozenset(MINOR_UNITS)


def is_valid_currency(code: str) -> bool:
    return isinstance(code, str) and code.upper() in VALID_CURRENCIES


def minor_units(code: str) -> int:
    return MINOR_UNITS[code.upper()]


def has_valid_precision(code: str, amount: Decimal) -> bool:
    """True if `amount` does not have more decimal places than the currency allows."""
    exponent = amount.normalize().as_tuple().exponent
    if not isinstance(exponent, int):  # NaN / Infinity
        return False
    decimals = -exponent if exponent < 0 else 0
    return decimals <= minor_units(code)


def quantize(code: str, amount: Decimal) -> Decimal:
    """Round-trip an amount to the currency's canonical precision for storage."""
    places = minor_units(code)
    quant = Decimal(1) if places == 0 else Decimal(1).scaleb(-places)
    return amount.quantize(quant)
