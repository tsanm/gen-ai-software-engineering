"""Author CLI tests — exercise the paycli command-line surface (covers cli.py)."""

from __future__ import annotations

from paycli.cli import main


def test_total(capsys):
    assert main(["total", "10", "20", "30"]) == 0
    assert capsys.readouterr().out.strip() == "60.0"


def test_average(capsys):
    assert main(["average", "10", "20", "30"]) == 0
    assert capsys.readouterr().out.strip() == "20.0"


def test_average_empty_via_cli(capsys):
    assert main(["average"]) == 0
    assert capsys.readouterr().out.strip() == "0.0"


def test_check_limit_exactly_at_limit(capsys):
    assert main(["check-limit", "60", "40", "100"]) == 0
    assert capsys.readouterr().out.strip() == "True"


def test_check_limit_over(capsys):
    assert main(["check-limit", "60", "41", "100"]) == 0
    assert capsys.readouterr().out.strip() == "False"


def test_export_plain_file(tmp_path, monkeypatch, capsys):
    src = tmp_path / "in.txt"
    src.write_text("hello")
    monkeypatch.chdir(tmp_path)
    assert main(["export", str(src)]) == 0
    assert (tmp_path / "report.txt").read_text() == "hello"
