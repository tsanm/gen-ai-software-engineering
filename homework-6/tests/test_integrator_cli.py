"""Tests for the integrator CLI surface and seeding helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import integrator
from agents.common import PipelinePaths
from integrator import seed_input


def test_seed_input_writes_one_file_per_record(base_txn: dict[str, Any], tmp_path: Path) -> None:
    paths = PipelinePaths.create(tmp_path / "shared")
    seed_input([base_txn, {**base_txn, "transaction_id": "TXN998"}], paths)
    files = list(paths.input.glob("*.json"))
    assert len(files) == 2


def test_main_runs_and_reports_ok(
    sample_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    # Redirect integrator.main to use isolated paths via __file__ relocation.
    fake_here = tmp_path / "hw"
    fake_here.mkdir()
    (fake_here / "sample-transactions.json").write_text(
        sample_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    monkeypatch.setattr(integrator, "__file__", str(fake_here / "integrator.py"))

    rc = integrator.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "all 3 transactions appear" in out
    assert (fake_here / "shared" / "results").is_dir()


def test_load_transactions_rejects_non_list(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")
    with pytest.raises(ValueError):
        integrator.load_transactions(path)
