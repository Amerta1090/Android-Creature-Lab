"""Unit tests — R-003 Config system (PRD §R-003).

Covers: defaults stable & non-mutating; layering precedence (defaults < user
file < env); deep-merge keeps default siblings; type/range/choice validation
with clear dotted-path messages; unknown-key warnings; `config set` round-trip;
CLI wiring (`validate` exit 0/5, `show` deterministic, `set` persists).
"""

from __future__ import annotations

import json

import pytest

from android_creature import config
from android_creature.cli import main


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _write_user(tmp_path, data: dict) -> None:
    path = tmp_path / "data" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _chdir(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)


def _load(tmp_path, monkeypatch, *, user: dict | None = None, env: dict | None = None):
    _chdir(tmp_path, monkeypatch)
    if user is not None:
        _write_user(tmp_path, user)
    return config.load_config_with_warnings(env=env or {})


# --------------------------------------------------------------------------- #
# defaults
# --------------------------------------------------------------------------- #

def test_defaults_valid_and_match_module_defaults(tmp_path, monkeypatch) -> None:
    merged, warnings = _load(tmp_path, monkeypatch)
    assert merged == config.DEFAULTS
    assert warnings == []
    assert config.validate_config(merged) == []


def test_load_never_mutates_shared_defaults(tmp_path, monkeypatch) -> None:
    merged, _ = _load(tmp_path, monkeypatch)
    merged["actions"]["experimental"] = True
    merged["pokedex"]["max_snapshots"] = 1
    again, _ = _load(tmp_path, monkeypatch)
    assert again == config.DEFAULTS
    assert config.DEFAULTS["actions"]["experimental"] is False
    assert config.DEFAULTS["pokedex"]["max_snapshots"] == 50


# --------------------------------------------------------------------------- #
# layering precedence
# --------------------------------------------------------------------------- #

def test_user_file_overrides_defaults(tmp_path, monkeypatch) -> None:
    merged, warnings = _load(
        tmp_path, monkeypatch, user={"logging": {"level": "debug"}}
    )
    assert merged["logging"]["level"] == "debug"
    # untouched siblings keep defaults
    assert merged["logging"]["format"] == config.DEFAULTS["logging"]["format"]
    assert merged["actions"]["experimental"] is False
    assert warnings == []


def test_env_overrides_user_file(tmp_path, monkeypatch) -> None:
    merged, _ = _load(
        tmp_path,
        monkeypatch,
        user={"logging": {"level": "info"}},
        env={"ACL_LOGGING_LEVEL": "debug"},
    )
    assert merged["logging"]["level"] == "debug"


def test_env_typed_values(tmp_path, monkeypatch) -> None:
    merged, _ = _load(
        tmp_path,
        monkeypatch,
        env={
            "ACL_ACTIONS_EXPERIMENTAL": "true",
            "ACL_POKEDEX_MAX_SNAPSHOTS": "200",
        },
    )
    assert merged["actions"]["experimental"] is True
    assert merged["pokedex"]["max_snapshots"] == 200


def test_deep_merge_keeps_default_siblings(tmp_path, monkeypatch) -> None:
    merged, _ = _load(
        tmp_path,
        monkeypatch,
        user={"actions": {"allowed_apps": {"com.foo": "MainActivity"}}},
    )
    assert merged["actions"]["allowed_apps"] == {"com.foo": "MainActivity"}
    assert merged["actions"]["enabled_levels"] == ["safe"]  # default sibling intact
    assert merged["actions"]["cooldowns"] == {}


# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #

def test_invalid_type_rejected_with_clear_message(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"actions": {"experimental": "yes"}})
    with pytest.raises(config.ConfigError) as excinfo:
        config.load_config()
    message = str(excinfo.value)
    assert "actions.experimental" in message
    assert "expected bool" in message


def test_invalid_range_rejected(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"pokedex": {"max_snapshots": 0}})
    with pytest.raises(config.ConfigError) as excinfo:
        config.load_config()
    assert "pokedex.max_snapshots" in str(excinfo.value)
    assert "expected int" in str(excinfo.value)


def test_invalid_choice_rejected(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"logging": {"level": "verbose"}})
    with pytest.raises(config.ConfigError) as excinfo:
        config.load_config()
    message = str(excinfo.value)
    assert "logging.level" in message
    assert "expected one of" in message
    assert "verbose" in message


def test_device_map_values_validated(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"devices": {"S1": {"mode": "banana"}}})
    with pytest.raises(config.ConfigError) as excinfo:
        config.load_config()
    assert "devices.S1.mode" in str(excinfo.value)


def test_unknown_keys_warned_not_fatal(tmp_path, monkeypatch) -> None:
    merged, warnings = _load(
        tmp_path, monkeypatch, user={"pokedex": {"typo_field": 1}}
    )
    assert merged["pokedex"].get("typo_field") is None
    assert any("pokedex.typo_field" in w and "unknown key" in w for w in warnings)


# --------------------------------------------------------------------------- #
# config set round-trip
# --------------------------------------------------------------------------- #

def test_set_path_roundtrip(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    config.set_config_path("logging.level", "debug")
    merged, _ = config.load_config_with_warnings()
    assert merged["logging"]["level"] == "debug"
    # default siblings survive a re-load of the user file
    assert merged["actions"]["experimental"] is False


def test_set_path_creates_parent_dir(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    config.set_config_path("pokedex.snapshot_dir", "tmp/snap")
    assert (tmp_path / "data" / "config.json").exists()


def test_set_invalid_value_persists_then_fails_validate(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    config.set_config_path("logging.level", "loud")
    with pytest.raises(config.ConfigError):
        config.load_config()
    assert config.validate_config(config.load_user_config()) != []


# --------------------------------------------------------------------------- #
# CLI wiring
# --------------------------------------------------------------------------- #

def test_cli_validate_ok_exit0(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["config", "validate"]) == 0
    assert "config OK" in capsys.readouterr().out


def test_cli_validate_bad_exit5(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"actions": {"experimental": "yes"}})
    assert main.creature(["config", "validate"]) == config.CONFIG_ERROR_EXIT
    captured = capsys.readouterr()
    assert "config error" in captured.err
    assert "actions.experimental" in captured.err


def test_cli_show_deterministic_order(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    main.creature(["config", "show"])
    first = capsys.readouterr().out
    main.creature(["config", "show"])
    second = capsys.readouterr().out
    assert first == second
    # sorted keys: "actions" precedes "creatures" precedes "devices" ...
    assert '"actions"' in first and '"devices"' in first


def test_cli_show_path(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    _write_user(tmp_path, {"pokedex": {"max_snapshots": 7}})
    assert main.creature(["config", "show", "pokedex.max_snapshots"]) == 0
    assert capsys.readouterr().out.strip() == "7"


def test_cli_set_then_validate(tmp_path, monkeypatch, capsys) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["config", "set", "pokedex.max_snapshots", "100"]) == 0
    assert "config set" in capsys.readouterr().out
    assert main.creature(["config", "validate"]) == 0
    merged = config.load_config()
    assert merged["pokedex"]["max_snapshots"] == 100


def test_cli_unknown_subcommand_exit1(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["config", "nonsense"]) == 1


def test_cli_set_missing_args_exit1(tmp_path, monkeypatch) -> None:
    _chdir(tmp_path, monkeypatch)
    assert main.creature(["config", "set", "logging.level"]) == 1