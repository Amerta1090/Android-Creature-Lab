"""Console entry points: `creature` and `pokedex` (PRD R-002/R-003/R-004).

Both accept `--version` (prints package version, exit 0) per the version smoke
gate, and `-v`/`--verbose` (enable debug logs, PRD R-004 acceptance).
`creature config <show|validate|set>` is the R-003 config surface:

- ``show [path]``      print the merged config (deterministic, sorted) or one dotted path
- ``validate``         exit 0 on a valid config, exit 5 on an invalid one
- ``set path value``   write ``value`` (JSON types when parseable) into ``data/config.json``

Deeper subcommands (scan/observe/run) arrive in later milestones.
"""

from __future__ import annotations

import json
import sys

import android_creature
from android_creature import config
from android_creature import errors
from android_creature import logging as logging_mod

USAGE = """\
{prog} — Android Creature → Pokédex

usage: {prog} [--version] [-v|--verbose] [config <show|validate|set> ...]

Logs go to stderr (format `HH:MM:SS.mmm LEVEL component message`); machine
output to stdout. `-v`/`--verbose` enables debug logs; the default level comes
from the `logging` config section. Subcommands (`scan`, `observe`, `run`, …)
arrive with their respective milestones.
"""

CONFIG_USAGE = """\
usage: {prog} config <show|validate|set>

  show [path]                 print merged config (or one dotted path), sorted
  validate                    exit 0 if valid, exit 5 on invalid config
  set <dotted.path> <value>   write value into data/config.json (JSON types)
"""

_VERBOSE_FLAGS = ("-v", "--verbose")


def _configure(verbose: bool) -> None:
    """Set up the project logger (R-004): debug when -v, else config default."""
    logging_mod.configure_logging(level="debug" if verbose else None)


def _emit_warnings(warnings: list[str]) -> None:
    for warning in warnings:
        print(f"config warning: {warning}", file=sys.stderr)


def _run_config(prog: str, argv: list[str]) -> int:
    sub = argv[0] if argv else ""
    try:
        if sub == "show":
            merged, warnings = config.load_config_with_warnings()
            _emit_warnings(warnings)
            if len(argv) > 1:
                try:
                    print(config.get_path(merged, argv[1]))
                except KeyError:
                    print(f"config error: unknown path {argv[1]!r}", file=sys.stderr)
                    return 1
            else:
                print(json.dumps(merged, indent=2, sort_keys=True))
            return 0
        if sub == "validate":
            merged, warnings = config.load_config_with_warnings()
            _emit_warnings(warnings)
            print("config OK")
            return 0
        if sub == "set":
            if len(argv) != 3:
                print(CONFIG_USAGE.format(prog=prog))
                return 1
            value = config.parse_value(argv[2])
            config.set_config_path(argv[1], value)
            config.load_config_with_warnings()  # re-validate the merged result
            print(f"config set: {argv[1]} = {json.dumps(value, sort_keys=True)}")
            return 0
        print(CONFIG_USAGE.format(prog=prog))
        return 1
    except config.ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return config.CONFIG_ERROR_EXIT


def _run(prog: str, argv: list[str]) -> int:
    try:
        return _run_inner(prog, argv)
    except errors.LabError as exc:
        # R-007 acceptance: top-level handler → one-line message + mapped exit.
        print(f"error: {exc}", file=sys.stderr)
        return errors.to_exit_code(exc)


def _run_inner(prog: str, argv: list[str]) -> int:
    if "--version" in argv or "-V" in argv:
        print(f"{prog} {android_creature.__version__}")
        return 0
    verbose = any(flag in argv for flag in _VERBOSE_FLAGS)
    _configure(verbose)
    args = [arg for arg in argv if arg not in _VERBOSE_FLAGS]
    if args and args[0] == "config":
        return _run_config(prog, args[1:])
    # Unknown flag / extra args → print usage, exit 1 (version smoke uses exit 0 only).
    sys.stdout.write(USAGE.format(prog=prog))
    return 1 if argv else 0


def creature(argv: list[str] | None = None) -> int:
    return _run("creature", list(sys.argv[1:] if argv is None else argv))


def pokedex(argv: list[str] | None = None) -> int:
    return _run("pokedex", list(sys.argv[1:] if argv is None else argv))