"""Structured logging (PRD R-004).

Events/logs go to **stderr**; machine output stays on **stdout** (the two
streams are never mixed — "never duplicates stdout frames").

Surface:

- :func:`get_logger` — the single import surface every module uses
  (DoD: all modules log through this; enforced by convention + R-009 lint).
- :func:`configure_logging` — one-time/idempotent setup: level (from the
  merged config ``logging.level`` or an explicit override) and format.

Line shape (config ``logging.format`` template):
``HH:MM:SS.mmm LEVEL component message`` e.g.::

    14:03:09.527 INFO android_creature.adb device connected

The timestamp is rendered by the stdlib logging boundary (this module never
imports ``time``/``datetime``); core logic reads time only via the injected
clock (PRD NFR-2 / R-005).

Failure mode (PRD R-004): stdlib logging config headaches → this stays a thin
wrapper — a single ``StreamHandler`` on ``sys.stderr``, no custom handlers.
"""

from __future__ import annotations

import logging
import sys

from android_creature import config

#: Canonical template documented in the config defaults (R-003). It describes
#: the line shape; :data:`DEFAULT_FORMAT` is the concrete %-style spec that
#: renders it.
TEMPLATE_DEFAULT = "HH:MM:SS.mmm LEVEL component message"

#: %-style format producing exactly ``TEMPLATE_DEFAULT``'s shape.
DEFAULT_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s %(name)s %(message)s"

DATE_FMT = "%H:%M:%S"

DEFAULT_LEVEL = "info"

_ROOT_NAME = "android_creature"

_LEVELS: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def _config_values() -> tuple[str, str]:
    """(level, format) from the merged config; defaults on absence/error.

    An invalid config must never crash logging setup — the ``config`` CLI
    reports it properly with exit 5. Unknown/absent keys fall back to defaults.
    """
    level, fmt = DEFAULT_LEVEL, DEFAULT_FORMAT
    try:
        cfg = config.load_config()
    except config.ConfigError:
        return level, fmt
    logging_cfg = cfg.get("logging", {})
    level = logging_cfg.get("level", DEFAULT_LEVEL) or DEFAULT_LEVEL
    template = logging_cfg.get("format", TEMPLATE_DEFAULT) or TEMPLATE_DEFAULT
    if template != TEMPLATE_DEFAULT:  # user-specified %-format escape hatch
        fmt = template
    return level, fmt


def configure_logging(level: str | None = None, format_spec: str | None = None) -> None:
    """Configure the shared logger: level + format + a single stderr handler.

    Idempotent: repeated calls replace the handler instead of stacking new
    ones, so a line is never emitted twice. ``level=None`` reads the merged
    config ``logging.level`` (default ``info``). ``format_spec`` overrides the
    config template when given.
    """
    cfg_level, cfg_fmt = _config_values()
    if format_spec:
        cfg_fmt = format_spec
    resolved_level = level or cfg_level
    if resolved_level not in _LEVELS:
        raise ValueError(
            f"unknown log level {resolved_level!r}; "
            f"expected one of {sorted(_LEVELS)}"
        )

    root = logging.getLogger(_ROOT_NAME)
    root.setLevel(_LEVELS[resolved_level])
    root.propagate = False  # one handler, no stdlib root duplication
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(cfg_fmt, datefmt=DATE_FMT))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return the project logger for ``name`` (e.g. ``"adb"``, ``"creature"``).

    The component shown in the line is the full dotted name
    (``android_creature.<name>``). Logging is active once the entry point
    called :func:`configure_logging`; until then records are buffered by
    stdlib (convention enforced by R-009 lint).
    """
    return logging.getLogger(f"{_ROOT_NAME}.{name}")