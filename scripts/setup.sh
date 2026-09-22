#!/usr/bin/env bash
# Dev bootstrap (PRD R-009): create .venv and install the package editable.
# Deterministic, offline-friendly (no network needed after package download).
set -euo pipefail

cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "error: python3 not found on PATH" >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "creating .venv with $PY …"
    "$PY" -m venv .venv
fi

echo "installing package (editable, dev extras) …"
.venv/bin/python -m pip install --disable-pip-version-check -q -e ".[dev]"

echo "OK — ready: make test · make lint"