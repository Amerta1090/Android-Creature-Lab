# Android Creature Lab

A host-side autonomous agent runtime (Python) that treats a connected Android
device as the *environment* of a small digital creature — plus a device
observability subsystem ("Pokédex") that gives the creature and the user
structured, semantic knowledge of that device.

## Two-phase vision

1. **A creature living on my Android.** The creature perceives device state
   (battery, screen, CPU, RAM, foreground app, network), keeps internal stats
   (energy, mood, curiosity, stress), decides deterministically (no LLM in the
   loop), acts through a strict safety allowlist, and remembers over time.
2. **A programmable digital organism with a model of its Android.** The Pokédex
   inventories packages, permissions, components, and runtime state; captures
   snapshots; diffs them; and derives change history + a stable device
   fingerprint that the creature consumes as a *semantic model* — not raw shell
   text.

Everything is local-first, deterministic-where-practical, ADB-driven, and
simulator-testable without hardware.

## Quickstart (3 bullets)

- **Setup:** `./scripts/setup.sh` creates a `.venv` and installs the package
  (`pip install -e .[dev]`) — no device or network required.
- **Test & lint:** `make setup && make test && make lint` runs the full suite
  green from a clean checkout, entirely offline.
- **Run:** `creature config validate` (config stack) and later
  `creature run` / `pokedex scan` talk to a connected Android device via adb.

See `docs/PRD.md` for the full plan, `docs/status.md` for progress, and
`docs/adr/README.md` for the architecture decision records (index + template
for writing new ADRs).
