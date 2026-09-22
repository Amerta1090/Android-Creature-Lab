"""Unit tests — R-004 Structured logging (PRD §R-004).

Covers: level filtering (config ``logging.level``, force via ``-v``/``--verbose``);
format ``HH:MM:SS.mmm LEVEL component message`` (time prefix, level, logger
name/component, message); stderr-only routing (never duplicates stdout frames);
idempotent ``configure_logging`` (no duplicated handler lines); config-driven
level; unknown level rejected.

Determinism: assertions match the shape of the line (a time prefix like
HH:MM:SS.mmm), never the wall-clock value itself — the timestamp is rendered by
the stdlib logging boundary, not by core logic (PRD NFR-2 / R-005 gate).
"""

from __future__ import annotations

import re

import pytest

from android_creature import config
from android_creature import logging as logging_mod
from android_creature.cli import main

_TIME_LINE = re.compile(
    r"^\d{2}:\d{2}:\d{2}\.\d{3} "
    r"(DEBUG|INFO|WARNING|ERROR) "
    r"(\S+) (.*)$"
)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _chdir(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)


def _write_user(tmp_path, data: dict) -> None:
    path = tmp_path / "data" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(__import__("json").dumps(data), encoding="utf-8")


def _emitted(capsys) -> tuple[str, str]:
    captured = capsys.readouterr()
    return captured.out, captured.err


# --------------------------------------------------------------------------- #
# shape + routing
# --------------------------------------------------------------------------- #

def test_info_line_has_required_fields(capsys) -> None:
    logging_mod.configure_logging("info")
    logging_mod.get_logger("perception").info("boot complete")
    out, err = _emitted(capsys)
    assert err  # logs land on stderr
    assert "boot complete" not in out  # never duplicated to stdout
    line = err.strip()
    match = _TIME_LINE.match(line)
    assert match is not None, f"line does not match format template: {line!r}"
    level, component, message = match.groups()
    assert level == "INFO"
    assert component == "android_creature.perception"
    assert message == "boot complete"


def test_warning_and_error_levels_rendered(capsys) -> None:
    logging_mod.configure_logging("debug")
    logging_mod.get_logger("adb").warning("slow transport")
    logging_mod.get_logger("actions").error("safety blocked")
    _, err = _emitted(capsys)
    assert "WARNING" in err and "slow transport" in err
    assert "ERROR" in err and "safety blocked" in err


# --------------------------------------------------------------------------- #
# level filtering
# --------------------------------------------------------------------------- #

def test_info_level_hides_debug(capsys) -> None:
    logging_mod.configure_logging("info")
    logger = logging_mod.get_logger("creature")
    logger.debug("hidden debug trace")
    logger.info("visible info")
    _, err = _emitted(capsys)
    assert "hidden debug trace" not in err
    assert "visible info" in err


def test_debug_level_shows_debug(capsys) -> None:
    logging_mod.configure_logging("debug")
    logging_mod.get_logger("creature").debug("full trace")
    _, err = _emitted(capsys)
    assert "full trace" in err


def test_error_level_hides_warning_and_info(capsys) -> None:
    logging_mod.configure_logging("error")
    logger = logging_mod.get_logger("creature")
    logger.info("quiet")
    logger.warning("quiet too")
    logger.error("loud")
    _, err = _emitted(capsys)
    assert "quiet" not in err
    assert "loud" in err


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #

def test_configure_reads_level_from_config(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"logging": {"level": "warning"}})
    logging_mod.configure_logging()  # level from config file
    logger = logging_mod.get_logger("creature")
    logger.info("muted by config")
    logger.warning("allowed by config")
    _, err = _emitted(capsys)
    assert "muted by config" not in err
    assert "allowed by config" in err


def test_configure_is_idempotent_no_duplicate_frames(capsys) -> None:
    logging_mod.configure_logging("info")
    logging_mod.configure_logging("info")  # second call must not stack handlers
    logging_mod.get_logger("creature").info("single frame")
    _, err = _emitted(capsys)
    assert err.count("single frame") == 1


def test_unknown_level_rejected() -> None:
    with pytest.raises(ValueError):
        logging_mod.configure_logging("loud")


# --------------------------------------------------------------------------- #
# CLI wiring: -v / --verbose (PRD R-004 acceptance)
# --------------------------------------------------------------------------- #

def test_cli_default_hides_debug(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["config", "validate"]) == 0
    logging_mod.get_logger("cli").debug("hidden without -v")
    _, err = _emitted(capsys)
    assert "hidden without -v" not in err


def test_cli_short_v_shows_debug(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["-v", "config", "validate"]) == 0
    logging_mod.get_logger("cli").debug("visible with -v")
    _, err = _emitted(capsys)
    assert "visible with -v" in err
    assert "DEBUG" in err


def test_cli_long_verbose_shows_debug(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["--verbose", "config", "validate"]) == 0
    logging_mod.get_logger("cli").debug("visible with --verbose")
    _, err = _emitted(capsys)
    assert "visible with --verbose" in err


def test_cli_verbose_keeps_machine_vs_log_streams_separate(
    tmp_path, monkeypatch, capsys
) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["-v", "config", "validate"]) == 0
    logging_mod.get_logger("cli").debug("stderr-only frame")
    out, err = _emitted(capsys)
    assert "stderr-only frame" in err
    assert "stderr-only frame" not in out
    assert "config OK" in out  # machine output stays on stdout


def test_cli_bad_config_still_exits_5_with_verbose(
    tmp_path, monkeypatch, capsys
) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"actions": {"experimental": "yes"}})
    assert main.creature(["-v", "config", "validate"]) == config.CONFIG_ERROR_EXIT
    captured = capsys.readouterr()
    assert "config error" in captured.err
    assert "actions.experimental" in captured.err