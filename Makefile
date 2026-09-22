# Makefile — dev runner + lint gates (PRD R-009)

PY         ?= python3
VENV       ?= .venv
PYTHON      = $(VENV)/bin/python
PYTEST      = $(PYTHON) -m pytest

.PHONY: setup test test-hw lint record-fixture clean

## Bootstrap: create .venv + editable install (idempotent; offline-friendly).
setup:
	./scripts/setup.sh

## Fast, offline test suite: unit + sim + adapter + regression (no hardware).
## hw-marked tests are excluded here; run `make test-hw` with a device attached.
test:
	$(PYTEST) tests -m "not hw"

## Hardware-required tests (device attached needed). No-op until M1/A-005.
test-hw:
	$(PYTEST) -m hw

## Quality gates: byte-compile everything, then src hygiene
## (no wall-clock/global-random tokens, stdlib-only imports).
lint:
	$(PYTHON) -m compileall -q src tests
	$(PYTHON) scripts/check_src_hygiene.py

## Record an adb fixture (offline replay data). Wiring lands with A-005.
record-fixture:
	@echo "record-fixture: wired in A-005 (fixture transport)."
	@echo "planned usage: pokedex record --device <serial> --label <label>"

## Remove generated artifacts (venv, caches, recordings).
clean:
	rm -rf .venv
	rm -rf src/android_creature.egg-info
	find . -name __pycache__ -type d -prune -exec rm -rf {} +