"""Version smoke — R-002 / PRD §R-002: `creature --version` exits 0 and prints
the package version; `pokedex --version` exits 0 too (both console entry points
are gate bodies per R-002 DoD / R-009 exit criteria).
"""

import subprocess
import sys
from pathlib import Path

CREATURE_SCRIPTS = ("creature", "pokedex")


def _venv_bin(name: str) -> str:
    """The console script lives next to the interpreter running pytest."""
    return str(Path(sys.executable).parent / name)


def test_creature_version_exit_code() -> None:
    """`creature --version` must exit 0 (R-002 DoD)."""
    proc = subprocess.run(
        [_venv_bin("creature"), "--version"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0


def test_pokedex_version_exit_code() -> None:
    """`pokedex --version` must exit 0 (R-002 DoD, both entry points)."""
    proc = subprocess.run(
        [_venv_bin("pokedex"), "--version"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0
