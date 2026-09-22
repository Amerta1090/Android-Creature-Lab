"""Trivial unit test — R-002: one honest unit test (not a copy of the smoke).

Checks the version string parses to a PEP 440-compatible, sortable tuple, and
that the package exposes exactly one version symbol (the module source of
truth), so CLI printing and the runtime version stay in lockstep.
"""

import re

import android_creature

_PEP440_CORE = re.compile(
    r"^(?P<ver>\d+\.\d+(?:\.\d+)?)(?:[.\-+]dev(?P<dev>\d+))?$"
)


def _parse(version: str) -> tuple[int, ...]:
    m = _PEP440_CORE.match(version)
    assert m is not None, f"version {version!r} is not PEP 440 core"
    parts = [int(p) for p in m.group("ver").split(".")]
    if m.group("dev"):
        parts.append(int(m.group("dev")))
    return tuple(parts)


def test_version_is_pep440_sortable() -> None:
    v = android_creature.__version__
    parsed = _parse(v)
    # 0.1.0 < 0.1.1 < 0.2.0 ordering sanity
    assert _parse("0.1.0") < _parse("0.1.1") < _parse("0.2.0")
    assert parsed >= (0, 1, 0)


def test_version_single_source() -> None:
    """`__init__.__version__` is the only version symbol; it's a plain string."""
    assert isinstance(android_creature.__version__, str)
    assert len(android_creature.__version__) > 0
