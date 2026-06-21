"""Unit tests for the shared infrastructure (money, masking, messages)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from agents.common import (
    SUPPORTED_CURRENCIES,
    AgentError,
    Message,
    PipelinePaths,
    configure_audit_logger,
    iso_now,
    mask_account,
    mask_text,
    new_message_id,
    parse_money,
    quantize_money,
    read_message,
)


def test_parse_money_rejects_float() -> None:
    with pytest.raises(AgentError):
        parse_money(1.23)


def test_parse_money_from_string_is_exact() -> None:
    assert parse_money("0.1") + parse_money("0.2") == Decimal("0.3")


def test_parse_money_invalid_string() -> None:
    with pytest.raises(AgentError):
        parse_money("not-a-number")


def test_quantize_money_round_half_up() -> None:
    assert quantize_money(Decimal("1.005"), "USD") == Decimal("1.01")
    assert quantize_money(Decimal("2.675"), "EUR") == Decimal("2.68")


def test_quantize_money_zero_decimal_currency() -> None:
    # JPY has 0 minor units.
    assert quantize_money(Decimal("1234.56"), "JPY") == Decimal("1235")


def test_supported_currencies_excludes_bogus() -> None:
    assert "XYZ" not in SUPPORTED_CURRENCIES
    assert SUPPORTED_CURRENCIES["USD"] == 2


def test_mask_account_hides_body() -> None:
    assert mask_account("ACC-1001") == "****01"
    assert mask_account("") == "****"


def test_mask_text_keeps_prefix() -> None:
    masked = mask_text("Monthly rent payment", keep=4)
    assert masked.startswith("Mont")
    assert "rent" not in masked
    assert mask_text("") == ""


def test_iso_now_format() -> None:
    value = iso_now()
    assert value.endswith("Z")
    assert "T" in value


def test_new_message_id_unique() -> None:
    assert new_message_id() != new_message_id()


def test_message_roundtrip() -> None:
    msg = Message(
        source_agent="a",
        target_agent="b",
        message_type="transaction",
        data={"transaction_id": "T1"},
    )
    restored = Message.from_dict(msg.to_dict())
    assert restored.data["transaction_id"] == "T1"
    assert restored.source_agent == "a"


def test_message_from_dict_missing_field() -> None:
    with pytest.raises(AgentError):
        Message.from_dict({"message_id": "x"})


def test_message_write_and_read(tmp_path: Path) -> None:
    msg = Message(
        source_agent="a",
        target_agent="b",
        message_type="transaction",
        data={"transaction_id": "T2"},
    )
    path = msg.write(tmp_path)
    assert path.exists()
    loaded = read_message(path)
    assert loaded.data["transaction_id"] == "T2"


def test_message_write_custom_name(tmp_path: Path) -> None:
    msg = Message("a", "b", "transaction", {"x": 1})
    path = msg.write(tmp_path, name="custom.json")
    assert path.name == "custom.json"


def test_pipeline_paths_create(tmp_path: Path) -> None:
    paths = PipelinePaths.create(tmp_path / "shared")
    assert paths.input.is_dir()
    assert paths.processing.is_dir()
    assert paths.output.is_dir()
    assert paths.results.is_dir()


def test_configure_audit_logger_idempotent(tmp_path: Path) -> None:
    log = tmp_path / "audit.log"
    first = configure_audit_logger(log)
    handlers_after_first = len(first.handlers)
    second = configure_audit_logger(log)
    assert first is second
    assert len(second.handlers) == handlers_after_first
