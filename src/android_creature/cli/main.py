"""Console entry points: `creature` and `pokedex` (PRD R-002).

Both accept `--version` (prints package version, exit 0) per the version smoke
gate; deeper subcommands (scan/observe/run) are wired in later milestones.
"""

from __future__ import annotations

import sys

import android_creature

USAGE = """\
{prog} — Android Creature → Pokédex

usage: {prog} --version

Both `creature` and `pokedex` share this host-side runtime. Subcommands
(`scan`, `observe`, `run`, …) arrive with their respective milestones.
"""


def _run(prog: str, argv: list[str]) -> int:
    if "--version" in argv or "-V" in argv:
        print(f"{prog} {android_creature.__version__}")
        return 0
    # Unknown flag / extra args → print usage, exit 1 (version smoke uses exit 0 only).
    sys.stdout.write(USAGE.format(prog=prog))
    return 1 if argv else 0


def creature(argv: list[str] | None = None) -> int:
    return _run("creature", list(sys.argv[1:] if argv is None else argv))


def pokedex(argv: list[str] | None = None) -> int:
    return _run("pokedex", list(sys.argv[1:] if argv is None else argv))
