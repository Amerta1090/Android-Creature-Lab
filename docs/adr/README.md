# Architecture Decision Records

ADRs capture decisions that shape the project. They are **the record of why** —
every microtask spec in `docs/PRD.md` §O maps to one of these.

## Index

| ADR | Title | Decision (short) | Source (§0) |
|-----|-------|------------------|-------------|
| [ADR-001](ADR-001.md) | Python + stdlib-only runtime | Python 3.12+; stdlib + pytest only through M11 | 0.1, 0.10 |
| [ADR-002](ADR-002.md) | Host-side runtime | The creature runs on the host PC; device is a pure subject | 0.2 |
| [ADR-003](ADR-003.md) | adb CLI wrapper | Wrap the `adb` binary, serial-targeted, typed result | 0.3 |
| [ADR-004](ADR-004.md) | Storage: SQLite + JSON + JSONL | sqlite3 for events/memory/history; JSON for state/config/snapshots; JSONL for raw recordings | 0.6 |
| [ADR-005](ADR-005.md) | Determinism policy | Injected clock + seeded RNG + deterministic orderings + golden files | 0.7 |
| [ADR-006](ADR-006.md) | No LLM in the decision loop | Never in core; optional advisory layer later, feature-flagged | 0.8 |
| [ADR-007](ADR-007.md) | Poll + edge events | Adaptive polling (5 s active / 60 s idle); transitions → events | 0.5 |
| [ADR-008](ADR-008.md) | No-root baseline | Everything runs under uid `shell`; root gated EXPERIMENTAL | 0.4 |

## Template for future ADRs

Copy the block below into `docs/adr/ADR-XXX.md` (next free number). Requirements:
one page; sections exactly **Context / Decision / Consequences**; Status starts as
`Proposed` and flips to `Accepted` after user confirmation (prompt.md §5 / PRD §21.6).

```markdown
# ADR-XXX — <short title>

Status: Proposed | Accepted

Date: YYYY-MM-DD

## Context
<!-- What problem/force is this addressing? Which §0 default / PRD section does it map to? -->

## Decision
<!-- What did we choose? Be concrete (tech, interface, policy). -->

## Consequences
- **Positive:** ...
- **Negative:** ...
- **Neutral:** ...
```

## Rules

1. One ADR per decision; keep them small and reversible-looking (they *are* revisable).
2. An ADR is required for any architectural change (config change, new dependency,
   new non-stdlib runtime dep, root/experimental path, LLM usage) — prompt.md §5.
3. Update this index when adding an ADR.