"""Layered config system (PRD R-003).

Precedence (highest wins):

1. CLI flags            — ``creature config set <path> <value>`` writes to the
                          user layer below.
2. Environment          — ``ACL_*`` variables map to dotted paths: the first
                          ``_``-separated segment names the top-level section
                          and the remainder joins the inner key, e.g.
                          ``ACL_LOGGING_LEVEL`` → ``logging.level``,
                          ``ACL_POKEDEX_MAX_SNAPSHOTS`` → ``pokedex.max_snapshots``.
3. User file            — ``data/config.json`` (JSON only, no comments — see the
                          R-003 failure mode: accept JSON, document).
4. Built-in defaults    — ``DEFAULTS`` in this module.

Merging is a deep merge: nested dicts merge recursively, non-dict values replace.
Validation is declarative (``_SCHEMA``): typed leaf checks plus range/choice
checks, errors reported with full dotted paths, unknown keys reported as
warnings. Iteration/output is deterministic (``sort_keys`` everywhere).

``ConfigError`` lives here until R-007 promotes it into the project-wide error
taxonomy (``errors.to_exit_code``); CLI mapping of config failures → exit 5
already matches R-007's plan.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Mapping

#: Exit code for config failures (PRD R-003 acceptance: bad value → exit 5).
CONFIG_ERROR_EXIT = 5

#: Default user config file, relative to the working directory (PRD §G.5/G.6).
DEFAULT_CONFIG_FILE = "data/config.json"

_ENV_PREFIX = "ACL_"


class ConfigError(Exception):
    """Invalid configuration (missing/unreadable file, schema violation)."""


# --------------------------------------------------------------------------- #
# Declarative schema
# --------------------------------------------------------------------------- #

def _int(lo: int | None = None, hi: int | None = None) -> dict[str, Any]:
    return {"type": "int", "min": lo, "max": hi}


def _float(lo: float | None = None, hi: float | None = None) -> dict[str, Any]:
    return {"type": "float", "min": lo, "max": hi}


def _str(*choices: str) -> dict[str, Any]:
    return {"type": "str", "choices": list(choices) or None}


def _bool() -> dict[str, Any]:
    return {"type": "bool"}


def _list(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "list", "items": items}


def _map(key_hint: str, value: dict[str, Any]) -> dict[str, Any]:
    """Arbitrary-keyed dict whose *values* validate against ``value``."""
    return {"type": "map", "key_hint": key_hint, "value": value}


def _section(fields: dict[str, Any]) -> dict[str, Any]:
    """Fixed-key dict; unknown inner keys are warned (not fatal)."""
    return {"type": "section", "fields": fields}


_SCHEMA: dict[str, Any] = {
    # §G.5 `devices`: per-serial overrides (mode, poll cadence, fg scan toggle).
    "devices": _map(
        "device serial",
        _section(
            {
                "mode": _str("sim", "usb", "wifi"),
                "poll_fast_s": _int(1, 3600),
                "poll_idle_s": _int(1, 3600),
                "fg_scan_on": _bool(),
            }
        ),
    ),
    # §G.5 `creatures`: per-creature configuration (personality, seed, tick dt).
    "creatures": _map(
        "creature id",
        _section(
            {
                "personality_id": _str(),
                "seed": _int(),
                "tick_dt_sec": _float(0.1, 86400),
            }
        ),
    ),
    # §G.5 `actions`: safety levels, app allow-list, cooldowns, experimental.
    "actions": _section(
        {
            # §0 default: SAFE on by default; CONTROL gated via config.
            "enabled_levels": _list(_str("safe", "control", "experimental")),
            "allowed_apps": _map("package", _str()),
            "cooldowns": _map("action id", _int(0, 86400)),
            "experimental": _bool(),
        }
    ),
    # §G.5 `pokedex`: snapshot storage.
    "pokedex": _section(
        {
            "snapshot_dir": _str(),
            "max_snapshots": _int(1, 10000),
        }
    ),
    # §G.5 `logging`: level + deterministic format (R-004 renders this).
    "logging": _section(
        {
            "level": _str("debug", "info", "warning", "error"),
            "format": _str(),
        }
    ),
}

#: Built-in defaults (deep-copied on every load; never mutated in place).
DEFAULTS: dict[str, Any] = {
    "devices": {},
    "creatures": {},
    "actions": {
        "enabled_levels": ["safe"],
        "allowed_apps": {},
        "cooldowns": {},
        "experimental": False,
    },
    "pokedex": {
        "snapshot_dir": "data/snapshots",
        "max_snapshots": 50,
    },
    "logging": {
        "level": "info",
        "format": "HH:MM:SS.mmm LEVEL component message",
    },
}


# --------------------------------------------------------------------------- #
# Merge + env plumbing
# --------------------------------------------------------------------------- #

def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (deep copies, no mutation).

    The result is fully detached from ``base``/``override`` so shared module
    defaults can never leak between loads (R-003 DoD).
    """
    out = copy.deepcopy(dict(base))
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def parse_value(raw: str) -> Any:
    """Coerce a CLI/env string: JSON types when parseable, else raw string."""
    stripped = raw.strip()
    if not stripped:
        return stripped
    try:
        return json.loads(stripped)
    except ValueError:
        return stripped


def env_overrides(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Map ``ACL_*`` env vars to a config-shaped dict for merging."""
    source = os.environ if env is None else env
    out: dict[str, Any] = {}
    for name, raw in source.items():
        if not name.startswith(_ENV_PREFIX):
            continue
        key = name[len(_ENV_PREFIX) :].lower()
        if not key:
            continue
        section, sep, rest = key.partition("_")
        if not section:
            continue
        value = parse_value(raw)
        if sep and rest:
            _set_path(out, [section, rest], value)
        else:
            _set_path(out, [section], value)
    return out


def _set_path(target: dict[str, Any], path: list[str], value: Any) -> None:
    node = target
    for part in path[:-1]:
        node = node.setdefault(part, {})
    node[path[-1]] = value


# --------------------------------------------------------------------------- #
# File layer
# --------------------------------------------------------------------------- #

def user_config_path() -> Path:
    return Path(DEFAULT_CONFIG_FILE)


def load_user_config(path: Path | None = None) -> dict[str, Any]:
    """Read the user file into a dict; absent file → {}. Bad JSON → ConfigError."""
    p = path if path is not None else user_config_path()
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ConfigError(f"cannot read config file {p}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"config file {p}: top level must be a JSON object")
    return data


def set_config_path(dotted: str, value: Any, path: Path | None = None) -> dict[str, Any]:
    """Write ``value`` at ``dotted`` path into the user file (atomic replace).

    Returns the user-layer dict as written.
    """
    parts = dotted.split(".")
    if not parts or any(not part for part in parts):
        raise ConfigError(f"invalid config path: {dotted!r}")
    p = path if path is not None else user_config_path()
    current = load_user_config(p)
    _set_path(current, list(parts), copy.deepcopy(value))
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(current, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, p)
    return current


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def _type_name(node: Any) -> str:
    if isinstance(node, bool):
        return "bool"
    if isinstance(node, int):
        return "int"
    if isinstance(node, float):
        return "float"
    if isinstance(node, str):
        return "str"
    if isinstance(node, list):
        return "list"
    if isinstance(node, dict):
        return "object"
    if node is None:
        return "null"
    return type(node).__name__


def _dot(path: list[str]) -> str:
    return ".".join(path)


def check_config(cfg: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    """Validate a merged config → (errors, warnings). Errors use dotted paths."""
    errors: list[str] = []
    warnings: list[str] = []

    def walk(node: Any, spec: dict[str, Any], path: list[str]) -> None:
        kind = spec["type"]
        if kind == "section":
            if not isinstance(node, dict):
                errors.append(f"{_dot(path)}: expected object, got {_type_name(node)}")
                return
            for key, child in spec["fields"].items():
                if key in node:
                    walk(node[key], child, path + [key])
            for key in node:
                if key not in spec["fields"]:
                    warnings.append(f"{_dot(path + [key])}: unknown key (ignored)")
        elif kind == "map":
            if not isinstance(node, dict):
                errors.append(
                    f"{_dot(path)}: expected object of {spec['key_hint']} → value, "
                    f"got {_type_name(node)}"
                )
                return
            for key, child in node.items():
                walk(child, spec["value"], path + [str(key)])
        elif kind == "list":
            if not isinstance(node, list):
                errors.append(f"{_dot(path)}: expected list, got {_type_name(node)}")
                return
            for index, item in enumerate(node):
                walk(item, spec["items"], path + [str(index)])
        else:
            _check_leaf(node, spec, path, errors)

    walk(cfg, {"type": "section", "fields": _SCHEMA}, [])
    return errors, warnings


def _check_leaf(node: Any, spec: dict[str, Any], path: list[str], errors: list[str]) -> None:
    kind = spec["type"]
    if kind == "int":
        lo, hi = spec["min"], spec["max"]
        ok = isinstance(node, int) and not isinstance(node, bool)
        if ok and lo is not None and node < lo:
            ok = False
        if ok and hi is not None and node > hi:
            ok = False
        if not ok:
            bounds = f" in [{lo}, {hi}]" if (lo is not None or hi is not None) else ""
            errors.append(
                f"{_dot(path)}: expected int{bounds}, got {_type_name(node)}"
            )
    elif kind == "float":
        lo, hi = spec["min"], spec["max"]
        ok = isinstance(node, (int, float)) and not isinstance(node, bool)
        if ok and lo is not None and node < lo:
            ok = False
        if ok and hi is not None and node > hi:
            ok = False
        if not ok:
            bounds = f" in [{lo}, {hi}]" if (lo is not None or hi is not None) else ""
            errors.append(f"{_dot(path)}: expected float{bounds}, got {_type_name(node)}")
    elif kind == "str":
        ok = isinstance(node, str)
        if ok and spec["choices"] and node not in spec["choices"]:
            errors.append(
                f"{_dot(path)}: expected one of {sorted(spec['choices'])}, got {node!r}"
            )
        elif not ok:
            errors.append(f"{_dot(path)}: expected str, got {_type_name(node)}")
    elif kind == "bool":
        ok = isinstance(node, bool)
        if not ok:
            errors.append(f"{_dot(path)}: expected bool, got {_type_name(node)}")


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #

def validate_config(cfg: Mapping[str, Any]) -> list[str]:
    """Errors only (empty == valid). Used by `creature config validate` + tests."""
    errors, _ = check_config(cfg)
    return errors


def unknown_keys(cfg: Mapping[str, Any]) -> list[str]:
    """Warnings only (unknown keys are ignored, never fatal)."""
    _, warnings = check_config(cfg)
    return warnings


def load_config(
    user_path: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Merge defaults < user file < env, validate, drop unknown keys.

    Raises ConfigError when the merged config is invalid.
    """
    merged, _ = load_config_with_warnings(user_path, env)
    return merged


def load_config_with_warnings(
    user_path: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Like :func:`load_config` but also returns unknown-key warnings."""
    merged = deep_merge(DEFAULTS, load_user_config(user_path))
    merged = deep_merge(merged, env_overrides(env))
    errors, warnings = check_config(merged)
    if errors:
        raise ConfigError("invalid configuration:\n  - " + "\n  - ".join(errors))
    return sanitize(merged), warnings


def sanitize(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with unknown section keys dropped (they were warned on).

    Mirrors the schema walk; map (arbitrary-keyed) entries are preserved.
    """
    out: dict[str, Any] = {}
    for key, node in cfg.items():
        if key not in _SCHEMA:
            continue  # unknown top-level key — warned, ignored
        out[key] = _sanitize_node(node, _SCHEMA[key])
    return out


def _sanitize_node(node: Any, spec: dict[str, Any]) -> Any:
    kind = spec["type"]
    if kind == "section" and isinstance(node, dict):
        return {
            key: _sanitize_node(node[key], spec["fields"][key])
            for key in node
            if key in spec["fields"]
        }
    if kind == "map" and isinstance(node, dict):
        return {key: _sanitize_node(value, spec["value"]) for key, value in node.items()}
    if kind == "list" and isinstance(node, list):
        return [_sanitize_node(item, spec["items"]) for item in node]
    return copy.deepcopy(node)


def get_path(cfg: Mapping[str, Any], dotted: str) -> Any:
    """Follow a dotted path like ``pokedex.max_snapshots`` (raises KeyError)."""
    node: Any = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(dotted)
        node = node[part]
    return node