"""Domain-component tests for the extensibility / compliance seams.

These cover behavior that isn't reachable through the default-region HTTP path
(alternate regions, the FX seam, PII masking, the compliance policy).
"""
from decimal import Decimal

import pytest

from src.compliance import CompliancePolicy, mask_account
from src.currencies import has_valid_precision
from src.models import TransactionCreate, TxType
from src.regions import DEFAULT_ACCOUNT_RE, IdentityRateProvider, Region, get_region
from src.validators import validate_transaction


def test_mask_account_variants():
    assert mask_account(None) is None
    assert mask_account("") == ""
    assert mask_account("ACC-12345") == "ACC-1****"
    assert mask_account("AB") == "A*"  # short identifier still partly masked


def test_region_restricts_to_allowed_currencies():
    region = Region("XX", "USD", DEFAULT_ACCOUNT_RE, allowed_currencies=frozenset({"USD"}))
    payload = TransactionCreate(fromAccount="ACC-12345", toAccount="ACC-67890",
                                amount=Decimal("10"), currency="EUR", type=TxType.transfer)
    fields = {d["field"] for d in validate_transaction(payload, region)}
    assert "currency" in fields  # EUR rejected in a USD-only region


def test_identity_rate_provider():
    provider = IdentityRateProvider()
    assert provider.convert(Decimal("10"), "USD", "USD") == Decimal("10")
    with pytest.raises(NotImplementedError):
        provider.convert(Decimal("10"), "USD", "EUR")


def test_compliance_policy_flags_large_amount():
    policy = CompliancePolicy(Decimal("1000"))
    assert policy.review(Decimal("1500")) == ["large_transaction"]
    assert policy.review(Decimal("1000")) == ["large_transaction"]  # boundary inclusive
    assert policy.review(Decimal("999.99")) == []


def test_precision_rejects_non_finite():
    assert has_valid_precision("USD", Decimal("NaN")) is False


def test_get_region_falls_back_to_default():
    assert get_region("NONEXISTENT").code == "DEFAULT"
    assert get_region("JP").code == "JP"
