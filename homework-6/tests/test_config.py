"""Tests for the declarative pipeline config and that agents read from it."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from agents import compliance_checker, fraud_detector, settlement_processor
from agents.common import DEFAULT_CONFIG_PATH, AgentError, load_config


def test_default_config_loads_and_has_expected_shape() -> None:
    cfg = load_config()
    assert cfg["stage_order"][0] == "transaction_validator"
    assert cfg["stage_order"][-1] == "reporting_agent"
    assert cfg["compliance"]["reporting_threshold"] == 10000
    assert cfg["coverage_floor"] == 80
    assert "USD" in cfg["currencies"]


def test_load_config_rejects_non_object(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(AgentError):
        load_config(bad)


def test_default_config_path_points_at_repo_file() -> None:
    assert DEFAULT_CONFIG_PATH.name == "pipeline.config.json"
    assert DEFAULT_CONFIG_PATH.exists()


def test_agent_thresholds_match_config() -> None:
    """The constants the agents expose are derived from pipeline.config.json."""

    cfg = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    assert cfg["fraud"]["review_threshold"] == fraud_detector.REVIEW_THRESHOLD
    assert cfg["fraud"]["medium_threshold"] == fraud_detector.MEDIUM_THRESHOLD
    assert (
        Decimal(str(cfg["compliance"]["reporting_threshold"]))
        == compliance_checker.REPORTING_THRESHOLD
    )
    assert Decimal(str(cfg["settlement"]["fee_rate"])) == settlement_processor.FEE_RATE
    assert set(compliance_checker.BLOCKED_ACCOUNTS) == set(cfg["compliance"]["blocked_accounts"])
