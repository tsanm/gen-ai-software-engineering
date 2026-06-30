"""Author baseline suite — encodes the CORRECT behaviour of paycli.

TDD contract: these tests are written BEFORE the fix. They are **RED pre-fix**
(they fail on the seeded BUG-A / BUG-B) and must be **GREEN post-fix**. The
bug-fixer runs this suite after each change; the unit-test-generator later ADDS
FIRST tests (e.g. the VULN-1 injection-blocked test) without duplicating these.
"""

from paycli import transactions as tx


def test_limit_exactly_at_limit_is_allowed():
    # BUG-A: a spend landing exactly on the limit must be ALLOWED.
    assert tx.is_within_daily_limit(60.0, 40.0, 100.0) is True


def test_limit_over_is_rejected():
    assert tx.is_within_daily_limit(60.0, 41.0, 100.0) is False


def test_limit_under_is_allowed():
    assert tx.is_within_daily_limit(60.0, 39.0, 100.0) is True


def test_average_of_empty_is_zero():
    # BUG-B: an empty input must not raise; the average is 0.
    assert tx.average_transaction([]) == 0


def test_average_basic():
    assert tx.average_transaction([10.0, 20.0, 30.0]) == 20.0


def test_total_basic():
    assert tx.total([10.0, 20.0, 30.0]) == 60.0
