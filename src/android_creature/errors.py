"""Error taxonomy (PRD R-007) — typed, predictable failures + exit codes.

Every failure a user can hit maps to a :class:`LabError` subclass carrying an
``exit_code``; :func:`to_exit_code` resolves it through the MRO, so a forgotten
subclass mapping falls back to :data:`DEFAULT_EXIT_CODE` (1) instead of
crashing the CLI.

Exit codes (PRD §R-007):
- :class:`ConfigError`        → 5 (invalid configuration; R-003 acceptance)
- :class:`NoDeviceError`      → 3 (no device / ambiguous serial)
- :class:`SafetyBlockedError` → 4 (action blocked by safety gate, PRD CR-05)
- :class:`AdbError` + kinds   → 1 (adb transport failures; A-001 refines)
- anything else               → 1 (default)

Kinds are kept as typed subclasses so callers can branch on intent
(``AdbTimeoutError`` → retry, ``AdbMissingBinaryError`` → install adb, …).

The CLI top-level handler (``cli.main``) catches ``LabError`` and prints one
line + ``to_exit_code`` — no raw tracebacks on the happy failure path.
"""

from __future__ import annotations

from typing import Any

DEFAULT_EXIT_CODE = 1


class LabError(Exception):
    """Base for all project failures."""

    exit_code: int = DEFAULT_EXIT_CODE


class ConfigError(LabError):
    """Invalid configuration (missing/unreadable file, schema violation).

    Consolidated here from ``config.py`` in R-007; ``config.ConfigError`` is
    an alias to this exact type.
    """

    exit_code = 5


class AdbError(LabError):
    """Base for adb transport/device failures (default exit code 1)."""


class AdbMissingBinaryError(AdbError):
    """``adb`` executable not found on PATH."""


class AdbTransportError(AdbError):
    """adb shell/command failed (nonzero exit, stderr, connection hiccup)."""


class AdbTimeoutError(AdbError):
    """adb command exceeded its timeout (PRD A-001 SUBPROCESS_TIMEOUT)."""


class AdbDeviceError(AdbError):
    """Device-level problem: offline, unauthorized, typo serial."""


class NoDeviceError(LabError):
    """No device available or the serial is ambiguous (PRD A-002)."""

    exit_code = 3


class SafetyBlockedError(LabError):
    """An action was rejected by the safety gate (PRD CR-05 / §0 default)."""

    exit_code = 4


class ParseError(LabError):
    """A parser failed on unparseable input; ``details`` carries context."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.details = details


def to_exit_code(exc: BaseException) -> int:
    """Map ``exc`` to its exit code via the class MRO (default 1)."""
    return int(getattr(type(exc), "exit_code", DEFAULT_EXIT_CODE))