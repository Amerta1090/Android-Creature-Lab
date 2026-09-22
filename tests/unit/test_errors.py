"""Unit tests — R-007 Error taxonomy (PRD §R-007).

Covers: ``LabError`` base with typed subclasses; ``to_exit_code`` mapping
(ConfigError→5, NoDeviceError→3, SafetyBlockedError→4, unmapped/adb→1);
``AdbError`` kind subclasses (missing binary / transport / timeout / device);
``ParseError`` carries details; exception chaining keeps ``__cause__``;
CLI top-level handler maps a raised ``LabError`` to its exit code plus a
one-line stderr message (R-007 acceptance); config ``ConfigError`` is the same
type as ``errors.ConfigError`` (consolidated in R-007).
"""

from __future__ import annotations

import pytest

from android_creature import config, errors
from android_creature.cli import main


# --------------------------------------------------------------------------- #
# taxonomy + exit code mapping
# --------------------------------------------------------------------------- #

def test_lab_error_is_base_class() -> None:
    assert issubclass(errors.LabError, Exception)
    assert issubclass(errors.ConfigError, errors.LabError)


def test_exit_code_mapping() -> None:
    assert errors.to_exit_code(errors.ConfigError("x")) == 5
    assert errors.to_exit_code(errors.NoDeviceError("x")) == 3
    assert errors.to_exit_code(errors.SafetyBlockedError("x")) == 4
    assert errors.to_exit_code(errors.LabError("x")) == 1


def test_adb_errors_default_to_one() -> None:
    kinds = [
        errors.AdbMissingBinaryError("adb not found"),
        errors.AdbTransportError("transport failed"),
        errors.AdbTimeoutError("timed out"),
        errors.AdbDeviceError("device offline"),
    ]
    for exc in kinds:
        assert isinstance(exc, errors.AdbError)
        assert errors.to_exit_code(exc) == 1


def test_unmapped_exception_defaults_to_one() -> None:
    assert errors.to_exit_code(ValueError("boom")) == 1


def test_exit_code_inherited_by_subclass() -> None:
    class _Sub(errors.NoDeviceError):
        pass

    assert errors.to_exit_code(_Sub("x")) == 3


# --------------------------------------------------------------------------- #
# messages + chaining + details
# --------------------------------------------------------------------------- #

def test_message_preserved() -> None:
    exc = errors.ConfigError("bad config value")
    assert str(exc) == "bad config value"


def test_chaining_keeps_cause() -> None:
    cause = ValueError("root cause")
    with pytest.raises(errors.ConfigError) as excinfo:
        try:
            raise ValueError("inner") from cause
        except ValueError:
            raise errors.ConfigError("wrapped") from cause
    assert excinfo.value.__cause__ is cause


def test_parse_error_keeps_details() -> None:
    exc = errors.ParseError("bad line", details={"line": 12, "raw": "x=y"})
    assert str(exc) == "bad line"
    assert exc.details == {"line": 12, "raw": "x=y"}
    assert errors.to_exit_code(exc) == 1


# --------------------------------------------------------------------------- #
# consolidation with config module
# --------------------------------------------------------------------------- #

def test_config_error_is_errors_config_error() -> None:
    assert config.ConfigError is errors.ConfigError
    assert config.CONFIG_ERROR_EXIT == errors.ConfigError.exit_code == 5


def test_config_raising_config_error_maps_to_exit_code(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "config.json").write_text(
        '{"actions": {"experimental": "yes"}}', encoding="utf-8"
    )
    with pytest.raises(errors.ConfigError):
        config.load_config()
    assert errors.to_exit_code(errors.ConfigError("invalid")) == 5


# --------------------------------------------------------------------------- #
# CLI top-level handler (acceptance)
# --------------------------------------------------------------------------- #

def test_cli_top_level_handler_maps_lab_error(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    def _boom(prog, argv):
        raise errors.NoDeviceError("no device attached")

    monkeypatch.setattr(main, "_run_config", _boom)
    assert main.creature(["config", "validate"]) == 3
    captured = capsys.readouterr()
    assert "no device attached" in captured.err
    assert "config OK" not in captured.out


def test_cli_top_level_handler_defaults_unmapped_to_one(
    monkeypatch, tmp_path, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    def real_boom(prog, argv):
        raise errors.LabError("generic failure")

    monkeypatch.setattr(main, "_run_config", real_boom)
    assert main.creature(["config", "validate"]) == 1
    assert "generic failure" in capsys.readouterr().err


def test_cli_config_error_still_exits_5(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "config.json").write_text(
        '{"pokedex": {"max_snapshots": 0}}', encoding="utf-8"
    )
    assert main.creature(["config", "validate"]) == 5
    assert "config error" in capsys.readouterr().err