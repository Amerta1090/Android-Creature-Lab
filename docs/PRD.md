# Android Creature → Pokédex — Project Plan (PRD + Technical Design + Backlog)

Status: Draft v0.1 · Date: 2026-09-22 · Owner: Lead Product Engineer

---

## 0. Assumptions & Resolved Decisions (resolved before planning completed)

Each row: Issue → Default decision → Why → Resolved-before-implementation (Y/N).

| # | Issue | Default decision | Why | Blocking? |
|---|-------|------------------|-----|-----------|
| 0.1 | Implementation language | **Python 3.12+** (3.14 available on host) | Stdlib-only core, fastest iteration, excellent test tooling (pytest), no build step, natural fit for ADB subprocess orchestration + JSON + SQLite. Rust/Go considered and rejected for iteration speed vs. maintainability of a hobby-scale project. | Yes |
| 0.2 | Where does the Creature run? | **On the host PC (the "Lab")**, not on the Android device | The Lab is the ecosystem; ADB is the interface. Running on-device would require shipping an app, on-device storage, and per-device install friction — none of which serve the "small autonomous software organism whose environment is the device" goal. The device stays a pure subject. | Yes |
| 0.3 | How to talk to the device | **Wrap the `adb` CLI binary** (serial-targeted subprocess) | Stable, standard, already installed (37.0.0). `pure-python-adb` rejected: extra dependency, TCP fragility, less transparent failures. A typed wrapper gives us timeouts, exit codes, determinism, and testability via a recording transport. | Yes |
| 0.4 | Root access | **No-root baseline.** Everything under uid `shell` (adb shell). Root/grant paths gated as EXPERIMENTAL, never required | Root is a deployment risk, varies by device/ROM, and most perception + safe actions work without it. | Yes |
| 0.5 | Observation mechanism | **Polling + edge detection.** Adaptive interval; transition detection produces events | ADB offers almost no push channels that are stable across versions. Poll cheap commands fast (5 s) while active, slow (60 s) when idle. logcat streaming deferred (M14 optional). | Yes |
| 0.6 | Persistence | **SQLite (stdlib `sqlite3`) for events/memory/history; JSON for state/config/snapshots; JSONL for raw adb recordings** | Queryable, transactional, zero-dependency, crash-safe (WAL). JSONL recording feeds regression fixtures. | Yes |
| 0.7 | Determinism | **Injected clock + seeded RNG + deterministic orderings + golden test files** | "Deterministic where practical" is a hard requirement (project philosophy). All decision logic takes time/seed as inputs; wall-clock only at the adapter boundary. | Yes |
| 0.8 | LLM usage | **Never in the decision loop.** Optional local analysis layer (e.g., llama.cpp) much later, feature-flagged, advisory-only | LLM in the core loop destroys determinism/testability and invites flaky behavior. Pokedex "explain like I'm 5" on recorded data is the only sanctioned place, far in the future. | Yes |
| 0.9 | Supported Android versions | **Nominal Android 10–16 (API 29–36)**; every parser degrades to `UNKNOWN` rather than failing; real support is defined by the test device(s) | ADB dumpsys output varies by version; tolerant parsers + recorded fixtures are the only honest approach. | Yes |
| 0.10 | Dependencies | **stdlib + pytest only through M11.** Optional UX deps (`rich`, matplotlib) require a ticket + justification | Minimal deps = maintainability. | Yes |
| 0.11 | Multi-device | **Serial-keyed from day one** (`-s <serial>` everywhere, config keyed by serial) | Avoids painful retrofit; cost is trivial. | Yes |
| 0.12 | Repository geometry | This directory (`Android Creature Lab/`) is the repo root; `git init` in M0 | No monorepo reuse with the unrelated WMS project in the parent dir. | Yes |

---

## A. Executive Summary

We build a **host-side autonomous agent runtime (Python)** that treats a connected Android device as the *environment* of a small digital creature, plus a **device anatomy/observability subsystem ("Pokédex")** that gives the creature — and the user — structured, semantic knowledge of that environment.

Two long-term, testable thesis statements:

1. *"A creature living on my Android"* — the Creature perceives device state (battery, temperature, screen, CPU, RAM, foreground app, network), maintains internal stats (energy, mood, curiosity, stress), decides (deterministic utility scoring, no LLM), acts through a strict allowlist (notification, vibration, brightness, volume, launching an allowlisted app…), and remembers (short-term events + long-term patterns).
2. *"A programmable digital organism with a model of its Android environment"* — the Pokédex inventories packages, permissions, components, and runtime state; captures snapshots; diffs them; derives a change history and a stable device fingerprint; and feeds the Creature a *semantic environment model* (`battery: 17%, charging: false, temperature: 31.2`) instead of raw shell text.

Everything is local-first, deterministic-where-practical, ADB-driven, simulator-testable without hardware, and built in 106 small verifiable microtasks across 15 milestones. The simulator (fake device) is a first-class citizen precisely so the decision engine can be validated without hardware, and so regressions can be reproduced forever.

Practical outcome after each milestone: M0 empty but running skeleton → M1 talks to a device → M3 a living (simulated) stat model → M7 a headless controllable simulation → M8 inventory scans → M10 snapshot/diff → M12 a creature living on a real device with a model of it → M14 hardened and documented.

---

## B. Product Definition

### What it is
- A **host-side engine** ("Android Creature Lab") that supervises one or more Android devices via ADB.
- A **deterministic creature simulation** (needs → perception → decision → action → memory).
- A **device observability + anatomy system** (Pokédex) producing structured inventories, snapshots, diffs, and history.
- An **integration layer** where the Creature consumes Pokédex semantics, not raw shell output.

### What it is NOT
- Not "a Tamagotchi app" — no cute-on-device UI, no gimmicks that only simulate life. The value is the *systems engineering*: state modeling, event ingestion, decision making, action execution, persistence, replay.
- Not an app installed on the device (ADR-002: LLM/core runs on host).
- Not a cloud service, not an LLM-driven chatbot, not a malware/automation toolkit (action allowlist, no unrestricted shell).
- Not a full Android UI-testing framework (no touch automation beyond optional `input tap` later, EXPERIMENTAL only).

### Principles (binding)
1. Local-first; no paid APIs; no cloud dependency.
2. Deterministic where practical; every decision explainable.
3. Small, verifiable steps; every task has a DoD.
4. Maintainability > cleverness; stdlib > dependencies.
5. A smaller working system beats a large broken one.

---

## C. User Stories

1. **As a developer, I want to run `creature simulate --scenario battery-low` so that I can verify the creature decides to sleep before ever touching a phone.**
2. **As a developer, I want `creature decisions --explain 42` to show the exact observation, internal state, candidate scores, and chosen action so that every decision is auditable.**
3. **As a user, I want `pokedex snapshot` then `pokedex diff a b` to tell me which apps were added/removed/updated and which permissions changed since I last looked.**
4. **As a user, I want `pokedex fingerprint` to give a stable fingerprint of my device so I can detect when the device identity changes (eg. factory reset, swapped device).**
5. **As a user, I want the creature to slow down its exploration at night (based on learned sleep windows) so it behaves plausibly over time.**
6. **As a user, I want the creature to send a notification on the phone when it "needs attention" (low energy, allowed by me) so it has a visible presence.**
7. **As a developer, I want the simulator to accept scripted device timelines (battery 90%→5%, screen on→off) so that decision behavior is regression-tested deterministically.**
8. **As a user, I want `creature run` to keep running across device disconnects and reconnects without crashing or corrupting state.**
9. **As a developer, I want recorded adb outputs (including malformed ones) as test fixtures so parsers are version-tolerant.**
10. **As a user, I want `pokedex history` to show me a timeline of significant changes (app installed 2026-09-01, permission change 2026-09-12) so the device's evolution is knowable.**

---

## D. Functional Requirements

Numbered, grouped. Creature = CR, Pokedex = PD, Lab/Common = LB.

### LB — Lab (common)
- LB-01 CLI entry points `creature` and `pokedex` with deterministic, JSON-able output.
- LB-02 Single config file (JSON), validated, layered (defaults < file < env < flags).
- LB-03 Structured logging to stderr; machine output to stdout only.
- LB-04 Injected clock; seeded RNG; all orderings deterministic.
- LB-05 Graceful handling of adb absence, device absence, timeouts, malformed output.
- LB-06 Every persistent write is atomic (temp file + rename; SQLite WAL).

### CR — Creature
- CR-01 Maintain internal stats: energy, mood, curiosity, stress (0–100 floats) + activity (`sleeping|resting|exploring|watching`).
- CR-02 Stat dynamics: decay/recovery over injected time; stress derived from perceivable threats (low battery, high temperature, night-time observer confusion).
- CR-03 Perception: consume latest Observation + derived facts (battery low, charging, screen off, device idle, temp high, foreground app).
- CR-04 Decision loop per tick: context → needs → candidates → utility scores → safety gate → select (deterministic, seedable) → execute → record.
- CR-05 Actions separated into SAFE / CONTROL / EXPERIMENTAL levels; only SAFE+CONTROL enabled by default; allowlist enforced at execution, never bypassable from decision code.
- CR-06 Every decision recorded as a DecisionRecord (observation, internal, scores, selected, safety, execution result, after-state) — replayable.
- CR-07 Short-term memory: recent events ring (bounded); long-term memory: extracted patterns (sleep window, frequent apps, battery behavior, crashes).
- CR-08 Memory consolidation runs on a schedule triggered by injected time, not wall-clock.
- CR-09 Personality: named config (default, night-owl, curious) that modulates utility weights — same seed+time+personality ⇒ same decision.
- CR-10 `creature status/observe/history/decisions/simulate/run/config/memory` CLI.

### PD — Pokédex
- PD-01 Identify device: model, manufacturer, Android/SDK version, ABI, build props, RAM/storage totals.
- PD-02 Package inventory: package name, versionName/code, apk path, enabled state, install/update time — with per-version parse tolerance.
- PD-03 Permissions: granted-per-status scan for each package (protection-level metadata only where cheaply available; marked optional).
- PD-04 Components: activities/services/receivers/providers with exported flag from `pm dump`.
- PD-05 Runtime: process list (pid, name, pkg, memory), CPU/mem summary, foreground app, battery/temp, network.
- PD-06 Snapshot capture (consistent-ish within a bounded window; stale fields marked).
- PD-07 Diff: added/removed/updated packages; permission granted/revoked; component changes; config changes.
- PD-08 History: snapshot timeline + derived change events (APPLICATION_ADDED/REMOVED/UPDATED, PERMISSION_CHANGED, COMPONENT_CHANGED, CONFIG_CHANGED).
- PD-09 Stable device fingerprint (JSON, hashable) from identity + build info.
- PD-10 `pokedex scan/apps/permissions/components/processes/runtime/snapshot/diff/history/fingerprint/record` CLI.
- PD-11 Every collector is a pure parser over recorded text ⇒ testable without hardware.

---

## E. Non-Functional Requirements

| NFR | Requirement |
|-----|-------------|
| NFR-1 Portability | Runs on Arch Linux (dev host). Python ≥3.12, no OS-specific deps. |
| NFR-2 Determinism | Same (seed, injected clock, inputs) ⇒ same decisions. Golden tests enforce. |
| NFR-3 Explainability | Every decision has a full trace; `--explain` renders it. |
| NFR-4 Reliability | Survives device disconnect/reconnect, adb restart, command timeouts, malformed output — without corrupting state (atomic writes, WAL). |
| NFR-5 Performance | Perception tick < 2 s for active mode; CLI cold start < 150 ms; scan of ~60 apps < 60 s. Measured by benchmark tests (N-004). |
| NFR-6 Security | No unrestricted shell; action allowlist enforced at execution layer; command templates with parameter validation (no shell injection); no root required. |
| NFR-7 Testability | All parsers/decisions testable without hardware; device-dependent tests tagged `hw` and skippable. |
| NFR-8 Maintainability | Stdlib-first; typed interfaces (dataclasses/TypedDict); schemas versioned; ADRs record decisions. |
| NFR-9 Resource footprint | Sim + creature runtime < 200 MB RAM, negligible disk (data dirs bounded, ring buffers capped). |
| NFR-10 Privacy | All data local; raw recordings are opt-in (`pokedex record`) and never leave the machine. |

---

## F. Architecture

```
┌──────────────────────────────┐
│       CLI / UI  (creature,   │
│        pokedex, --json)      │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│        Creature Core         │
│  State · Needs · Personality │
│  Decision Engine · Safety    │
│  Memory (short+long)         │
└──────────────┬───────────────┘
               │  semantic environment (Observations, Facts, Events)
┌──────────────▼───────────────┐
│         Pokédex              │
│  Identity · Inventory(perms/ │
│  components) · Runtime ·     │
│  Snapshot/Diff · History ·   │
│  Fingerprint                 │
└──────────────┬───────────────┘
               │  parsed Observations / raw recordings
┌──────────────▼───────────────┐
│      Android Adapter         │
│  AdbClient (serial-targeted) │
│  Perception (poll+edge) ·    │
│  Action executors            │
└──────────────┬───────────────┘
               │  adb shell (uid shell, no root)
               ▼
        Android device(s)
```

**Data flow (one tick):** `device → adb → parser → Observation → [store | edge-detector → Event] → Pokédex semantic model → Creature context → needs → candidates → scores → safety → action → result → DecisionRecord → memory`.

**Two execution modes:**
- `mode = sim` — Perception is a `FakeDevice` (scripted/random-but-seeded), actions are no-op backends. Everything else identical.
- `mode = device` — Perception is real ADB polling, actions are allowlisted executors.

**Module layout (top level)** — see §18 for the full tree.

**Key invariants:** decision code never touches subprocess/adb directly (adapter boundary); parsers never fail hard (UNKNOWN); actions never run unallowlisted (safety layer); wall-clock only at adapter boundary.

---

## G. Data Model

### G.1 Observation (perception tick; normalized, typed)
```
Observation {
  ts: ISO8601 (injected clock),
  battery:  { percent: int|null, status: "charging|discharging|full|not_charging|unknown",
              source: "ac|usb|wireless|none|unknown", temperature_c: float|null },
  power:    { screen: "on|off|dozing|unknown", wakefulness: "awake|asleep|dozing|unknown" },
  load:     { cpu_user_pct: float|null, cpu_idle_pct: float|null, load1: float|null },
  memory:   { total_kb: int|null, avail_kb: int|null, free_kb: int|null },
  storage:  { path: "/data", total_kb: int|null, free_kb: int|null },
  network:  { connected: bool|null, type: "wifi|mobile|vpn|none|unknown" },
  display:  { brightness: int|null, timeout_sec: int|null },
  device:   { uptime_sec: int|null, boot_epoch_sec: int|null },
  foreground:{ package: str|null, activity: str|null },
  orientation: "portrait|landscape|unknown",
  source: "sim" | "device", device_serial: str|null
}
```
`null` = parse failed or unavailable (never an exception). Missing fields default `unknown`.

### G.2 Derived facts (computed from Observation + previous tick)
`battery_low(<20)`, `battery_critical(<10)`, `charging`, `screen_on`, `device_idle` (screen off + no fg change + uptime stable over 2+ ticks), `temp_high(>40°C)`, `fg_app_changed`, `night` (injected local hour).

### G.3 CreatureState
```
CreatureState {
  schema_version: 1,
  creature_id: "c-0001",
  tick: int, ts: ISO8601,
  stats: { energy: 0..100, mood: 0..100, curiosity: 0..100, stress: 0..100 },
  activity: "sleeping|resting|exploring|watching",
  activity_since_tick: int,
  personality_id: str,
  last_decision_ref: {tick, id}|null
}
```
Transitions guard: e.g. `sleeping` only enterable when `energy < threshold` or `night`; wake on energy recovery or event. Stat ranges clamped; dynamics defined per-stat in a registry (pure functions of: stat, dt_ticks, context facts, personality — no I/O).

### G.4 DecisionRecord
```
DecisionRecord {
  decision_id, tick, ts,
  context: { observation: Observation, facts: [str], memory: {top_patterns:[...], recent_events:[...]} },
  internal: { stats_before: {...} },
  candidates: [ { action_id, params, score, reason } ],
  selected: { action_id, params } | null,
  safety: "allowed" | { "blocked": reason },
  execution: { status: "success|failed|blocked|skipped|pending", result: str|null, took_ms },
  stats_after: {...}
}
```

### G.5 Config
```
config.json {   # layered: defaults < data/config.json < env < CLI
  devices: { "<serial>": { mode, poll_fast_s, poll_idle_s, fg_scan_on, ... } },
  creatures: { "c-0001": { personality_id, seed, tick_dt_sec, ... } },
  actions: { enabled_levels: ["safe","control"], allowed_apps: {"pkg": "activity"}, cooldowns:{...}, experimental: false },
  pokedex: { snapshot_dir, max_snapshots, ... },
  logging: { level, format },
}
```

### G.6 Storage layout (runtime)
```
data/
  config.json
  devices/<serial>/
    creature_state.json          (atomic writes)
    lab.sqlite                   (events, decisions, patterns, pokedex tables, snapshot meta)
    snapshots/<uuid|name>.json
    recordings/<ts>-<label>.jsonl (raw adb out → fixtures; opt-in)
```
Snapshot payload JSON can exceed row size comfortably; metadata rows in SQLite reference files.

---

## H. Event Model

### H.1 Event types (normalized, schema-versioned)
Device/transport: `DEVICE_CONNECTED`, `DEVICE_DISCONNECTED`, `ADB_RESTARTED`, `COMMAND_TIMEOUT`, `PARSE_FALLBACK` (parser hit UNKNOWN — tracked for parser-quality metrics).
Battery/power: `BATTERY_LOW`, `BATTERY_CRITICAL`, `CHARGING_STARTED`, `CHARGING_STOPPED`, `TEMP_HIGH`, `SCREEN_ON`, `SCREEN_OFF`, `DEVICE_BOOTED` (uptime reset).
App/runtime: `APP_FOREGROUND(pkg)`, `APP_LAUNCHED(pkg)` (creature-initiated), `APP_INSTALLED`, `APP_REMOVED`, `APP_UPDATED`, `PERMISSION_CHANGED`, `COMPONENT_CHANGED`, `CONFIG_CHANGED` (last five from Pokédex diff, M10+).
Creature: `DECISION(decision_id)` (see DecisionRecord), `ACTION_STARTED`, `ACTION_SUCCEEDED`, `ACTION_FAILED`, `ACTION_BLOCKED` (safety), `MEMORY_CONSOLIDATED`, `STATE_PERSISTED`.

### H.2 Event flow
```
adapter(poll) ─► Observation ─► edge_detector ─► Event ─► event store (SQLite)
                                                  └─► organism runtime (async wake / tick trigger)
pokedex(diff) ─► ChangeSet ─► Event ─► event store ─► memory consolidation hook
```
Event schema: `{ id, ts, type, importance (0..1), payload_json, device_serial, source: "sim|device" }`.

### H.3 Polling vs events (resolved — see 0.5)
Poll every `poll_fast_s` when active (screen on / charging / recent event), `poll_idle_s` when idle. Events are produced by edge detection on consecutive Observations and by Pokédex diffs. No push channel dependency.

---

## I. Creature Behavior Model

### I.1 Stats (deliberately minimal)
| Stat | Meaning | Dynamics (at tick) | Inputs |
|------|---------|--------------------|--------|
| energy | reserves | −rate(activity); +rate if charging; recovery during sleep; low-threshold triggers sleep pressure | battery %, charging, activity |
| mood | hedonic tone | decays toward baseline; +charges on "good" events (screen on, app changed, charging), − on bad (temp high, battery low, repeated failures) | facts, event history |
| curiosity | drive to explore | +when fg app changes or screen on (novelty), − when idle/night | fg change, screen, night |
| stress | arousal/negativity | +temperature high, +battery critical, +repeated same-action failure; decays when stable/charging/sleeping | facts, action results |

**Dropped (with reason):** social need (no social input channel in v1), comfort (folded into mood/stress), health/status (derived, not stateful).

### I.2 Activity states
`sleeping` (low energy / night; energy recovers fastest; curiosity decays), `resting` (idle device, medium recovery), `exploring` (screen on / fg changes; curiosity up, energy down), `watching` (screen on, stable — low activity cost, low learning). Transitions are **guarded** (preconditions + hysteresis: enter sleep at energy<20, wake at energy>60) to avoid flapping.

### I.3 Perception → decision pipeline (deterministic)
```
context = { observation, facts, memory: top patterns + recent events, injected_time }
needs = evaluate_needs(context, stats)          # deficits: energy_demand, curiosity_demand, stress_relief ...
candidates = registry.candidates_for(context, stats, needs)
for c in candidates: c.score = utility(c, needs, stats, personality, seeded_noise(c.action_id))
safety_gate(candidates)                          # remove/flag blocked
selected = argmax(score)                         # deterministic tie-break: action_id lexical
if selected: execute(selected) → result          # via action backend (sim or adb)
record DecisionRecord; update stats; schedule memory consolidation if due
```

### I.4 Utility scoring
`score(a) = Σ w_i · need_component_i(a, context) + personality_mod(a) + noise(seed, tick, action_id)`.
Weights per personality (default: energy 0.45, curiosity 0.25, stress_relief 0.20, mood 0.10; night-owl shifts energy weight lower at night, etc.). Noise ∈ [−2,2] from seeded RNG — variety without nondeterminism (same seed ⇒ same run). Tie-break: higher `safety` level, then lexical action_id.

### I.5 Candidate actions (seed set; registry is data, easily extended)
| action_id | level | device effect | preconditions |
|-----------|-------|---------------|---------------|
| notify | SAFE | post notification via `cmd notification post` | cooldown |
| vibrate | SAFE | short vibration `cmd vibrator_manager vibrate` | cooldown |
| set_brightness | CONTROL | `settings put system screen_brightness` | screen on, daytime-ish, in allowed range |
| set_volume | CONTROL | `media volume --stream 3 --set N` | cooldown |
| launch_app | CONTROL | `am start -n` (allowlist map) | app allowlisted, energy high enough |
| toggle_battery_saver | EXPERIMENTAL | `settings put global low_power` | experimental flag on |
| open_url | CONTROL | `am start -a VIEW` (allowlist domains) | allowlisted domain |

All actions carry: params schema, cost (stat deltas on success, e.g. explore drains energy), cooldown, success parser, failure mapping.

### I.6 Memory
- **Short-term:** ring buffer of last N events (default 2000), each with importance 0..1 (type base weight × deviation boost, e.g. battery at 17% vs median → boost). Retention by count + time window; old entries archived to SQLite w/ decay.
- **Long-term:** pattern table `(pattern_type, key)`: `sleep_window` (night hours stats), `frequent_apps` (top by fg time), `battery_pattern` (typical lows/charging times), `crash_pattern` (app removed/updated shortly after install — "churn"), `action_affinity` (which actions succeed/blocked often).
- **Consolidation:** runs on injected-clock schedule (e.g., every 240 ticks or at first night tick when screen off, whichever earlier); reads short-term, updates patterns, prunes.
- **Querying:** `top_patterns(count)`, `recent_events(k, types)`, `summary()` — all deterministic (sorted, truncated identically).

### I.7 Behavior guidance (what makes it "interesting", not spammy)
- Sleep pressure rises sharply at low energy → creature visibly "naps" (notification muted, no actions).
- Curiosity drives app exploration only when energy is adequate; repeated failures raise stress and stop the action from being re-chosen (backoff).
- Learned night sleep window overrides action generation at night unless an important event (battery critical) forces wake.

---

## J. Pokédex Data Model

Tables in `lab.sqlite` (all keyed by `device_serial`):

| Table | Columns (key ones) | Notes |
|-------|--------------------|-------|
| device | serial, model, manufacturer, android_version, sdk, abi[], ram_total_kb, storage_total_kb, build_fingerprint, first_seen, last_seen, **FINGERPRINT_HASH** | one row per device; fingerprint = sha256 of stable props |
| package | pkg_name, version_name, version_code, apk_path, enabled, app_type, install_time, update_time, observed_at | PK (serial,pkg) |
| permission | pkg_name, permission, granted, protect_level(status where available), observed_at | PK (serial,pkg,permission) |
| component | pkg_name, component, kind(activity/service/receiver/provider), exported, observed_at | PK (serial,pkg,component,kind) |
| process | pid, name, pkg(guess via mapping), mem_kb, observed_at | per scan |
| snapshot | id, device_serial, ts, label, payload_path(json), schema_version, stale_fields[] | capture meta |
| change | device_serial, ts, kind(APPLICATION_ADDED/REMOVED/UPDATED, PERMISSION_GRANTED/REVOKED, COMPONENT_CHANGED, CONFIG_CHANGED, PACKAGE_ENABLED/DISABLED), detail_json, snapshot_from, snapshot_to | derived by diff/history |

**Semantic environment for the Creature** (final integration, M12):
```
EnvironmentModel {
  device: fingerprint-derived (model, sdk, ram, storage)
  apps: top-N frequent + allowlisted launchable {pkg, version}
  runtime: fg app, screen, battery, temp, network, load
  changes: recent ChangeSet entries (last 24h)
}
```
The Creature consumes `EnvironmentModel` (typed), never adb text.

---

## K. CLI Specification

### K.1 Conventions
- Two entry points: `creature`, `pokedex`; both from package `android_creature.cli` (console-scripts in pyproject).
- Default output: human tables/plain text to stdout; logs to stderr. `--json` = machine-readable only (JSON on stdout).
- `--device <serial>` (default: single connected device; error if ambiguous), `--config <path>`, `--timeout <sec>`, `-v/--verbose`, `--seed <int>` (creature commands).
- Exit codes: `0` ok · `1` runtime error · `2` usage error · `3` no device / adb unavailable · `4` safety/permission blocked · `5` config invalid.
- Determinism: lists sorted by stable keys; timestamps from injected clock; `--json` uses `sort_keys`.
- Errors: single-line `error: <message>` to stderr; never a traceback unless `-v`.

### K.2 `creature` commands
| Command | Args | Output |
|---------|------|--------|
| `creature status` | `--device/--sim` | table: stats, activity, since, personality, last decision, memory summary |
| `creature observe` | `--once` | one Observation + derived facts (or JSON) |
| `creature history` | `--limit N` `--type T` `--since ISO` | event log (ts, type, importance, payload) |
| `creature decisions` | `--limit N` `--explain ID` `--json` | decision records / full trace |
| `creature simulate` | `--scenario NAME` `--ticks N` `--seed S` `--timescale X` `--step` | run to completion (or step) printing periodic summaries + final state |
| `creature run` | `--sim` `--device S` `--once` `--watch` `--ticks N` | tick loop; watch = live section rendering |
| `creature config` | `show` `validate` `set key value` | config dump / validation report |
| `creature memory` | `dump` `stats` `--pattern TYPE` | short+long memory contents / stats |

### K.3 `pokedex` commands
| Command | Args | Output |
|---------|------|--------|
| `pokedex scan` | `--device` `--full` `--packages-only` | updates inventory tables; summary (N apps, N perms, N components) |
| `pokedex apps` | `--pattern` `--json` | table: pkg, version, enabled, install/update time |
| `pokedex permissions` | `--pkg` `--granted` `--revoked` | per-package permission table |
| `pokedex components` | `--pkg` `--type` | component + exported flags |
| `pokedex processes` | `--json` | pid/name/mem table |
| `pokedex runtime` | `--watch` `--interval S` | fg app, screen, battery, temp, network, load — one shot or stream |
| `pokedex snapshot` | `--name LABEL` | creates snapshot; prints id |
| `pokedex diff` | `A B` (ids) | ChangeSet table (kind, pkg, detail) |
| `pokedex history` | `--device` `--json` | timeline of changes from snapshots |
| `pokedex fingerprint` | `--json` | identity + fingerprint hash |
| `pokedex record` | `--label` `--command-pattern KEY` | capture raw adb outputs to recordings/ (for fixtures) |

### K.4 Command versioning
`creature --version`, `pokedex --version` print package version. CLI contract frozen at v1 after M0 (additive changes only; ADR if breaking).

---

## L. Testing Strategy

Layers (all under pytest, wired in M0):
1. **Unit** — pure logic: stat dynamics, needs, utility scoring, selector (incl. ties/empty), importance, diff engine, every parser (fixtures).
2. **Simulation** — fake device timelines; full decision loop; determinism (same seed/time ⇒ identical decision traces — golden files).
3. **Adapter** — recorded adb outputs + a **fixture transport** (maps command → recorded text), covering: normal, malformed, empty, timeout, exit≠0, Android-version variants.
4. **Regression** — golden decision traces + recorded device states; `pokedex diff` on curated snapshot pairs.
5. **Integration (`hw` marker)** — real device (skippable when absent): scan → snapshot → diff → creature run --once → action smoke.
6. **Failure** — adb missing, device offline/disconnect mid-scan, command timeout, permission denied, app disappearing during scan, reboot (uptime reset), battery NaN.

Rules: no network in tests; no wall-clock in tests (injected clock); every fixture is a checked-in text file under `tests/fixtures/adb/`; `make test` runs unit+sim+adapter+regression (fast, no device); `make test-hw` adds integration. Coverage floor on core (creature + parsers + diff): 85% (`.coveragerc`), enforced in M6+.

Determinism harness: `conftest.py` provides `seed`, `clock` fixtures; all randomness goes through `android_creature.rng`; golden files checked into `tests/regression/golden/`.

---

## M. Milestone Roadmap

Ordered; dependencies shown. (M0 → M1 → M2 → (M3 ∥ M8) → M4 → M6 → M5 → M7 → M9 → M10 → M11 → M12 → M13 → M14)

| # | Milestone | Entry criteria | Exit criteria (DoD at milestone level) | Depends on |
|---|-----------|----------------|----------------------------------------|------------|
| M0 | Repository / Architecture | empty repo | `make test` green (skeleton), `creature --version`/`pokedex --version` run, PRD + ADRs committed | — |
| M1 | Android Connection Layer | M0 | AdbClient + discovery + state machine + fixture transport; adapter tests pass offline | M0 |
| M2 | Device Perception | M1 | 8 observers + scheduler + edge detection + store; fixture-tested | M1 |
| M3 | Creature State | M0 | schema + dynamics + persistence; unit tests | M0 |
| M4 | Decision Engine | M3 | context→needs→candidates→scores→select loop; golden determinism | M3 |
| M5 | Creature Actions | M1, M4 | 6 actions + safety gate + cooldowns; sim + fixture tests | M1, M4 |
| M6 | Creature Memory | M4 | short/long-term + importance + consolidation; deterministic tests | M4 |
| M7 | Simulation | M4, M6 | scenario DSL + headless run + presets; full determinism | M4, M6 |
| M8 | Pokédex Inventory | M1 | identity + packages + perms + components collectors + CLI; fixture-tested | M1 |
| M9 | Pokédex Runtime | M1, M8 | processes + runtime monitor + CLI | M1, M8 |
| M10 | Snapshot / Diff | M8, M9 | snapshot capture + diff engine + CLI; curated diff tests | M8, M9 |
| M11 | Historical Device Model | M10 | history store + change derivation + fingerprint + CLI | M10 |
| M12 | Creature + Pokédex Integration | M7, M11 | EnvironmentModel bridge; creature works against real device via Pokédex | M7, M11 |
| M13 | UI / Visualization | M7 | status/decide explain/watch views; HTML history export | M7 (M12 optional) |
| M14 | Hardening / Documentation | M12 | failure injection + soak + docs + versioned release | M12 |

---

## N. Sprint Plan

15 sprints, one per milestone (S2 = M1, …, S15 = M14). Sprint length target ≈ 2–4 focused working sessions each. For every sprint, the exit criteria are the milestone exit criteria; a sprint is not "done" on code existence alone.

| Sprint | Milestone | Objective | Tasks | Key tests | Exit criteria |
|--------|-----------|-----------|-------|-----------|---------------|
| S1 | M0 | Repo, package, CI-lite, foundations | R-001…R-009 | skeleton pytest, version smoke | see R-009 DoD |
| S2 | M1 | Talk to Android via adb | A-001…A-007 | adapter/fixture tests | device connect/disconnect handled by state machine (fixture-tested) |
| S3 | M2 | Perceive device | P-001…P-013 | observer parse tests + edge tests | `creature observe` shows full Observation on sim + fixture |
| S4 | M3 | Creature state machine | C-001…C-005 | dynamics unit tests | state round-trips, transitions guarded |
| S5 | M4 | Decision engine | D-001…D-008 | determinism golden tests | same input ⇒ same decision |
| S6 | M5 | Actions + safety | X-001…X-011 | safety + fixture tests | blocked action never executes (test) |
| S7 | M6 | Memory | M-001…M-007 | importance/consolidation tests | patterns build under scripted events |
| S8 | M7 | Simulation | S-001…S-006 | scenario determinism | battery-low scenario behaves as specified |
| S9 | M8 | Pokédex inventory | K-001…K-008 | parser + CLI tests | `pokedex scan` populates DB from fixtures |
| S10 | M9 | Pokédex runtime | K2-001…K2-006 | runtime tests | `pokedex runtime --once` works on fixtures/hw |
| S11 | M10 | Snapshot/diff | DP-001…DP-005 | diff golden tests | `pokedex diff a b` correct on curated pairs |
| S12 | M11 | History/fingerprint | H-001…H-005 | history derivation tests | timeline correct after 3 synthetic snapshots |
| S13 | M12 | Integration | I-001…I-006 | sim E2E + hw smoke | creature consumes EnvironmentModel; full trace on real device |
| S14 | M13 | UI/viz | U-001…U-004 | render snapshot tests | decision explanations rendered; watch mode usable |
| S15 | M14 | Hardening/docs | N-001…N-006 | failure + soak + bench | 24 h soak green; docs complete; v1.0.0 tag |

---

## O. Full Microtask Backlog

Format per task: **ID — Title** / Purpose / Prereq / Scope / Files / Tests / Acceptance / DoD / Complexity / Deps / Failure modes.

Legend: Complexity S ≤ 1 session · M ≤ 2 · L ≥ 3. `hw` = needs physical device.

---

### M0 — Repository / Architecture (Sprint 1)

**R-001 — Initialize monorepo skeleton**
- Purpose: canonical starting point; everything else lands on top.
- Prereq: none.
- Scope: `git init`, `.gitignore` (venv, `data/`, `__pycache__`, recordings), top-level dirs (`docs/ src/ tests/ data/ scripts/`), `README.md` stub (project intent, 3 quickstart bullets), `LICENSE` (MIT).
- Files: `.gitignore`, `README.md`, `LICENSE`, empty dirs.
- Tests: none (layout assertion in R-002's smoke).
- Acceptance: `git status` clean on first commit; README renders.
- DoD: committed; dirs exist; README states the two-phase vision.
- Complexity: S · Deps: — · Failure: none material.

**R-002 — Python package skeleton + toolchain**
- Purpose: importable package with console entry points.
- Prereq: R-001.
- Scope: `pyproject.toml` (setuptools, `[project.scripts] creature=… pokedex=…`, pytest config, coverage config), `src/android_creature/__init__.py` (version), stub `cli/main.py` that prints version + usage, `.venv` + `pip install -e .[dev]` (pytest), `tests/conftest.py` (seed + clock fixtures).
- Files: `pyproject.toml`, `src/android_creature/__init__.py`, `src/android_creature/cli/main.py`, `tests/conftest.py`.
- Tests: `tests/smoke/test_version.py` (`creature --version` exit 0); one trivial unit test.
- Acceptance: `pip install -e .` works; both entry points run; `pytest` green.
- DoD: green `pytest`, entry points verified, venv reproducible via `scripts/setup.sh` (R-009).
- Complexity: M · Deps: R-001 · Failure: Python 3.14 vs setuptools edge cases → pin `setuptools>=75`; keep stdlib-only runtime deps.

**R-003 — Config system**
- Purpose: single validated JSON config, layered (defaults < `data/config.json` < env `ACL_*` < CLI flags).
- Prereq: R-002.
- Scope: `config.py`: load/merge/validate (schema dict, type+range checks), `config show/validate/set` wired to CLI stub; deterministic iteration; unknown-key warnings.
- Files: `src/android_creature/config.py`, `tests/unit/test_config.py`, CLI wiring in `main.py`.
- Tests: defaults; layering precedence; invalid values rejected with clear message; unknown keys warned.
- Acceptance: `creature config validate` passes on fresh install; a bad value fails with exit 5.
- DoD: precedence documented in module docstring; no mutable global defaultValue leakage between tests.
- Complexity: M · Deps: R-002 · Failure: mutable default dicts; JSON vs comments friction → accept JSON only (no comments), document.

**R-004 — Structured logging**
- Purpose: events/logs to stderr, machine output to stdout, deterministic formatting.
- Prereq: R-002.
- Scope: `logging.py`: `get_logger(name)`, levels, format `HH:MM:SS.mmm LEVEL component message`; `--verbose` in CLI; never duplicates stdout frames.
- Files: `src/android_creature/logging.py`, tests.
- Tests: level filtering; format contains required fields.
- Acceptance: `-v` shows debug; default hides it.
- DoD: all modules go through this logger (enforced by convention + lint).
- Complexity: S · Deps: R-002 · Failure: stdlib logging config headaches → thin wrapper, no custom handlers beyond StreamHandler.

**R-005 — Clock abstraction**
- Purpose: injectable time everywhere; determinism backbone.
- Prereq: R-002.
- Scope: `clock.py`: `Clock` protocol; `SystemClock`; `SimClock` (manual advance, `advance(sec)`, `now`, `tick_id`, `iso()`); global default = SystemClock, replaced in tests/sim.
- Files: `src/android_creature/clock.py`, tests.
- Tests: iso formatting; monotonicity; sim advance; no wall-clock imports in core (lint rule R-009).
- Acceptance: core modules use only injected clock.
- DoD: no `datetime.now()/time.time()` outside adapter/config test boundaries — enforced by grep check in `make lint`.
- Complexity: S · Deps: R-002 · Failure: accidental wall-clock use → lint.

**R-006 — Seeded RNG utility**
- Purpose: deterministic randomness; reproducibility.
- Prereq: R-002.
- Scope: `rng.py`: `SeededRng` per creature (`seed`), methods `rand_float(a,b)`, `choice(weighted)`, mixed with tick for per-tick stability; no module-level `random`.
- Files: `src/android_creature/rng.py`, tests.
- Tests: same seed ⇒ same stream; different seeds vary; weighted choice bounds.
- Acceptance: decision traces reproducible (validated in M4).
- DoD: single import surface for randomness.
- Complexity: S · Deps: R-002 · Failure: stdlib `random` leakage → lint + review.

**R-007 — Error taxonomy**
- Purpose: typed, predictable failures or exit codes.
- Prereq: R-002.
- Scope: `errors.py`: `LabError` base + `ConfigError` (exit 5), `AdbError` (missing binary, transport, timeout, device), `NoDeviceError` (3), `SafetyBlockedError` (4), `ParseError` details; `to_exit_code()`.
- Files: `src/android_creature/errors.py`, tests.
- Tests: mapping to exit codes; chaining keeps cause.
- Acceptance: CLI top-level handler maps exceptions to exit codes + one-line message.
- DoD: all public error paths covered by mapping test.
- Complexity: S · Deps: R-002 · Failure: forgetting to map → handler default to 1.

**R-008 — Docs skeleton + ADRs**
- Purpose: record decisions; keep plan in-repo.
- Prereq: R-001.
- Scope: commit `docs/PRD.md` (this document); `docs/adr/ADR-001…ADR-008.md` — 001 Python/stdlib, 002 host-side runtime, 003 adb CLI wrapper, 004 storage (SQLite+JSON+JSONL), 005 determinism policy, 006 no-LLM-in-loop, 007 poll+edge events, 008 no-root baseline. Each: Context / Decision / Consequences.
- Files: `docs/PRD.md`, `docs/adr/*.md`.
- Tests: none.
- Acceptance: each ADR one page; decisions match defaults in §0.
- DoD: committed; template for future ADRs documented in README.
- Complexity: S · Deps: R-001 · Failure: docs drift → ADR template mandates updates.

**R-009 — Dev runner + lint gates**
- Purpose: one command for test/lint/record; guards quality.
- Prereq: R-002, R-005.
- Scope: `Makefile` targets: `setup` (venv+install), `test` (unit+sim+adapter+regression; fast), `test-hw`, `lint` (`python -m compileall`, wall-clock grep, import-order of nothing-exotic), `record-fixture`; `scripts/setup.sh`.
- Files: `Makefile`, `scripts/setup.sh`, `tests/README.md`.
- Tests: `make test` from clean checkout.
- Acceptance: fresh clone → `make setup && make test` green without a device.
- DoD: documented in README; CI-lite (no cloud required; optional GH Actions config later under a ticket).
- Complexity: M · Deps: R-002, R-005 · Failure: make vs plain python → keep both documented.

### M1 — Android Connection Layer (Sprint 2)

**A-001 — AdbClient (wire wrapper)**
- Purpose: single typed surface over `adb -s <serial> shell …`; timeouts, exit codes, stderr capture, no shell injection.
- Prereq: R-007.
- Scope: `adb/transport.py`: `AdbClient(serial=None, timeout=10)`, `run(*args, input=None) -> AdbResult(stdout, stderr, returncode, elapsed)`, `shell(cmd)`; command arrays (no string interpolation); `SUBPROCESS_TIMEOUT` → `AdbTimeoutError`; smart retry flag later (A-003).
- Files: `src/android_creature/adb/transport.py`, tests (mock subprocess).
- Tests: normal, timeout, nonzero exit, missing binary, args never shell-joined.
- Acceptance: parser modules consume only `AdbResult`.
- DoD: no `shell=True` anywhere; timeout honored.
- Complexity: M · Deps: R-007 · Failure: adb hangs → timeout + kill; confirmed working on android-tools 37.

**A-002 — Device discovery + serial targeting**
- Purpose: know which devices exist; multi-device by serial from day one.
- Prereq: A-001.
- Scope: parse `adb devices -l` → `DeviceInfo{serial, model, state, usb?}`; `list_devices()`, `require_device(serial|None)` (None + exactly one ⇒ it; None + many ⇒ NoDeviceError ambiguous; none ⇒ NoDeviceError).
- Files: `adb/discovery.py`, tests (fixture lines).
- Tests: 0/1/n devices; offline state; malformed line ignored; ambiguous selection error.
- Acceptance: `pokedex scan --device` targets exactly one serial.
- DoD: deterministic ordering of lists (serial sort).
- Complexity: S · Deps: A-001 · Failure: `-l` output format varies → tolerate missing fields.

**A-003 — Connection state machine + supervision**
- Purpose: survive disconnect/reconnect; never corrupt state.
- Prereq: A-002.
- Scope: `ConnectionState` (disconnected→connecting→connected→degraded; reasons); supervision loop: on failure → backoff (1,2,4,8,15 s capped), re-verify via `adb devices`; emits DEVICE_CONNECTED/DISCONNECTED/ADB_RESTARTED events (H.1); `healthy()` gate for actions.
- Files: `adb/connection.py`, tests (fake client).
- Tests: offline mid-run recovered; repeated failures capped backoff; events emitted once each.
- Acceptance: `creature run` survives adb kill/device replug in fixture test.
- DoD: no retry storm; state transitions logged.
- Complexity: M · Deps: A-002 · Failure: ambiguity of "offline" vs "unauthorized" → treat both as disconnected + log reason.

**A-004 — Device info (getprop) reader**
- Purpose: base identity used everywhere.
- Prereq: A-001.
- Scope: `device.py`: read allowlist of props (`ro.product.model`, `ro.product.manufacturer`, `ro.build.version.release`, `ro.build.version.sdk`, `ro.product.cpu.abilist`, `ro.build.fingerprint`, `ro.serialno`); tolerant parse; `DeviceInfo` dataclass.
- Files: `adb/device.py`, fixture tests.
- Tests: normal props; missing prop → null field; weird values.
- Acceptance: `pokedex fingerprint --device` shows them (M11 wires fully).
- DoD: prop list is data (easy to extend).
- Complexity: S · Deps: A-001 · Failure: props missing on OEMs → null-tolerant.

**A-005 — Fixture transport (recorded adb)**
- Purpose: test the whole stack without hardware; feed by `pokedex record`.
- Prereq: A-001.
- Scope: `adb/fixture_transport.py`: maps command key → recorded text from `tests/fixtures/adb/<key>.txt`; records into `data/devices/<serial>/recordings/<ts>-<label>.jsonl` when enabled; `FixtureAdbClient` subclasses traffic? — implement as `Transport` interface (real + fixture + recording wrapper).
- Files: `adb/transport.py` (extract `Transport` base), `adb/fixture_transport.py`, `adb/recording_transport.py`, fixture files, tests.
- Tests: fixture lookup by key; missing key → explicit error; recording wrapper round-trip.
- Acceptance: adapter tests (A-006) run with `FIXTURES=1` and no adb.
- DoD: `pokedex record` produces replayable fixture files (Sprint 9).
- Complexity: M · Deps: A-001 · Failure: fixture opaqueness → every fixture file has header comment with source command + Android version.

**A-006 — Adapter tests (incl. malformed/timeout/version variants)**
- Purpose: prove tolerance.
- Prereq: A-005.
- Scope: for every A-task parser: normal, empty, malformed, truncated, Android-10-vs-15 variants where known; plus timeout and exit≠0 cases through fake transport.
- Files: `tests/adapter/*.py`, fixtures.
- Tests: the above matrix.
- Acceptance: all adapter tests green without device.
- DoD: every `UNKNOWN` fallback path exercised at least once.
- Complexity: M · Deps: A-005 · Failure: fixture drift vs real device → re-record with `pokedex record` + label.

**A-007 — Failure-mode tests (adb absent/offline/killed)**
- Purpose: harden M1.
- Prereq: A-003, A-006.
- Scope: tests simulating missing binary (PATH hijack), `device offline`, `adb server killed`, long command (timeout), `unauthorized`; assert typed errors + exit codes.
- Files: `tests/adapter/test_failures.py`.
- Tests: matrix above.
- Acceptance: mapped to `errors.py`; CLI messages actionable.
- DoD: all exit codes 1/3 paths verified.
- Complexity: M · Deps: A-003, A-006 · Failure: environment-dependent → simulated only, marked `# unit`.

### M2 — Device Perception (Sprint 3)

**P-001 — Observation schema**
- Purpose: single typed normalized structure (§G.1).
- Prereq: R-002.
- Scope: `perception/observation.py`: dataclasses + `to_dict/from_dict`, schema_version, `UNKNOWN` conventions, equality for tests.
- Files: schema module + tests.
- Tests: serialization round-trip; unknown defaults.
- Acceptance: all collectors emit this type.
- DoD: fields validated (types, ranges where defined).
- Complexity: S · Deps: R-002 · Failure: schema drift → versioned + `from_dict` strictness.

**P-002 — Battery observer (`dumpsys battery`)**
- Purpose: percent/status/source/temperature.
- Prereq: A-001, P-001.
- Scope: `observers/battery.py`: parse `dumpsys battery` (level, scale, status 2/3/4/5, ac/usb/wireless plugged, temperature tenths°C); units normalized; nulls on absence.
- Files: observer + `tests/fixtures/adb/dumpsys-battery-*.txt` + parser tests.
- Tests: full output; missing keys; weird status code; temperature 0 → null.
- Acceptance: `creature observe` shows battery block on fixtures.
- DoD: status mapped to enum; temperature → °C.
- Complexity: S · Deps: A-001, P-001 · Failure: `dumpsys battery` absent on some ROMs → whole block null, log PARSE_FALLBACK.

**P-003 — Screen/wakefulness observer**
- Purpose: is the device lit / awake.
- Prereq: A-001, P-001.
- Scope: `observers/screen.py`: parse `dumpsys power` (`mWakefulness=`, Display Power state) with ver-variant fallbacks; map to `on|off|dozing|unknown`.
- Files: observer + fixtures + tests.
- Tests: awake/asleep/dozing variants; missing line.
- Acceptance: screen block populated.
- DoD: two fallback patterns implemented.
- Complexity: S · Deps: A-001, P-001 · Failure: key renamed across versions → tolerant regex.

**P-004 — Foreground app observer**
- Purpose: what's in front.
- Prereq: A-001, P-001.
- Scope: `observers/fg_app.py`: `dumpsys window windows` (`mCurrentFocus`/`mFocusedApp`) + newer `dumpsys activity activities` (`ResumedActivity`) fallback; extract package+activity.
- Files: observer + fixtures (Android 10 & 15) + tests.
- Tests: both syntaxes; none found.
- Acceptance: fg block populated; `app_launched` edge in P-011.
- DoD: two strategies; null when ambiguous.
- Complexity: S · Deps: A-001, P-001 · Failure: shell limited apps invisible → null, documented.

**P-005 — CPU / load observer (`dumpsys cpuinfo`)**
- Purpose: load + user/idle percentages.
- Prereq: A-001, P-001.
- Scope: `observers/load.py`: parse overall block; first sample may be stale → two-sample delta optional later (note); totals normalized.
- Files: observer + fixtures + tests.
- Tests: standard output; missing totals.
- Acceptance: load block populated.
- DoD: `load1` from `uptime` too (P-009); percentages clamped 0..100.
- Complexity: S · Deps: P-002 pattern · Failure: format churn → tolerant.

**P-006 — Memory observer (`dumpsys meminfo`)**
- Purpose: total/avail/free RAM.
- Prereq: A-001, P-001.
- Scope: `observers/memory.py`: parse summary lines (`Total RAM:`, `Free RAM:`, `Avail RAM:` variants).
- Files: observer + fixtures + tests.
- Tests: variants; missing sections.
- Acceptance: memory block populated.
- DoD: kB normalization.
- Complexity: S · Deps: — · Failure: unit suffixes → normalize.

**P-007 — Storage observer (`df /data`)**
- Purpose: free/total storage of data partition.
- Prereq: A-001, P-001.
- Scope: `observers/storage.py`: `df -k /data` parsed (1k-blocks units).
- Files: observer + fixtures + tests.
- Tests: df output variants.
- Acceptance: storage block populated.
- DoD: parse by path row, not header position.
- Complexity: S · Deps: — · Failure: custom df on OEM → tolerant.

**P-008 — Network observer (`dumpsys connectivity`)**
- Purpose: connected? type?
- Prereq: A-001, P-001.
- Scope: `observers/network.py`: parse `Active default network:` / `NetworkAgentInfo` presence; type inference (wifi/mobile); tolerant.
- Files: observer + fixtures + tests.
- Tests: wifi active; no active; unparsable.
- Acceptance: network block populated or null.
- DoD: never throw; default unknown.
- Complexity: S · Deps: — · Failure: verbose format → keep to key lines.

**P-009 — Uptime/display/orientation observer**
- Purpose: uptime (boot detection), brightness/timeout, orientation.
- Prereq: A-001, P-001.
- Scope: `observers/misc.py`: `uptime` (`cat /proc/uptime` first field; fallback `uptime` command), `settings get system screen_brightness` & `screen_off_timeout`, `dumpsys input | grep SurfaceOrientation`.
- Files: observer + fixtures + tests.
- Tests: normal; missing.
- Acceptance: device block populated; boot reset detectable.
- DoD: three sub-collectors under one observer module.
- Complexity: S · Deps: — · Failure: /proc restricted → fallback.

**P-010 — Polling scheduler (adaptive)**
- Purpose: cheap cycle: fast when active, slow when idle.
- Prereq: P-001..P-009.
- Scope: `perception/scheduler.py`: tick loop with adaptive interval (config `poll_fast_s`/`poll_idle_s` + escalation rules), jitter **disabled** (determinism), tick bookkeeping.
- Files: scheduler + tests (SimClock).
- Tests: active→idle transition changes cadence; no drift storm.
- Acceptance: `creature run` ticks at configured rates in sim.
- DoD: pure function `next_interval(state)` unit-tested.
- Complexity: M · Deps: P-001, R-005 · Failure: idle misses events → edge detection still catches transitions on wake.

**P-011 — Edge detection → derived events**
- Purpose: observations become events (battery low, charging started, screen on, app foreground changed…).
- Prereq: P-002..P-009, H.1 schema.
- Scope: `perception/edge.py`: pure `detect(prev: Observation, cur: Observation, ticks) -> [Event]`; event normalization store-compatible.
- Files: edge module + tests.
- Tests: each transition type; no duplicate spam; hysteresis notes.
- Acceptance: `BATTERY_LOW` fired once crossing 20 (with latch).
- DoD: pure function; unit-tested table-driven.
- Complexity: M · Deps: P-001 · Failure: flicker → event latch (min cooldown per type).

**P-012 — Observation store**
- Purpose: append + query observations; feed history/debug.
- Prereq: R-002.
- Scope: `perception/observer_store.py` (SQLite `observation` table, capped retention).
- Files: store + tests.
- Tests: append/query window; cap trimming.
- Acceptance: `creature history` includes observations.
- DoD: deterministic query order.
- Complexity: S · Deps: R-002 · Failure: disk growth → cap + prune job.

**P-013 — Perception end-to-end tests**
- Purpose: whole perception stack against fixtures.
- Prereq: P-010..P-012.
- Scope: full fake-transport perception pass → Observation with all blocks; replay of recorded session → identical Observation sequence (determinism).
- Files: `tests/adapter/test_perception_e2e.py`, recordings fixture.
- Tests: full coverage matrix.
- Acceptance: `creature observe` works in `--sim` and fixture mode.
- DoD: 100% of Observation fields populated-or-null-documented in at least one test.
- Complexity: M · Deps: P-010..P-012 · Failure: stale fixtures → re-record.

### M3 — Creature State (Sprint 4)

**C-001 — CreatureState schema**
- Purpose: typed state (§G.3).
- Prereq: R-002.
- Scope: `creature/state.py`: dataclass, clamps, valid activity enum, `to_dict/from_dict` w/ schema_version, equality.
- Files: state module + tests.
- Tests: round-trip; clamp behavior; version guard.
- Acceptance: any module uses this type for state.
- DoD: no raw dicts in creature internals.
- Complexity: S · Deps: R-002 · Failure: version drift → explicit migration hook.

**C-002 — State persistence**
- Purpose: crash-safe save/load.
- Prereq: C-001.
- Scope: `creature/state_store.py`: atomic JSON writes (tmp+rename+fsync), load w/ validation, corrupt file → backup + fresh state + PARSE_FALLBACK event.
- Files: store + tests.
- Tests: save/load; corrupt file recovery; schema-version mismatch.
- Acceptance: kill -9 mid-save never yields corrupt live state.
- DoD: atomicity verified by test simulating crash.
- Complexity: M · Deps: C-001 · Failure: partial write → atomic rename mitigates.

**C-003 — Activity state machine**
- Purpose: guarded transitions with hysteresis.
- Prereq: C-001.
- Scope: `creature/activity.py`: activity enum, transition guard table (`sleeping` enter energy<20 or night; wake energy>60 or (screen on + energy>35); rest→explore on fg change; watch→explore on novelty), `since_tick` tracking, hysteresis windows.
- Files: activity module + tests.
- Tests: each guard; hysteresis edge (no flapping at boundary ±1); illegal transitions rejected.
- Acceptance: activity reflects sleep/wake cycles in sim.
- DoD: guard table data-driven; all branches tested.
- Complexity: M · Deps: C-001 · Failure: flapping at thresholds → hysteresis.

**C-004 — Stat dynamics registry**
- Purpose: four stats with pure dynamics (§I.1).
- Prereq: C-001, C-003.
- Scope: `creature/dynamics.py`: per-stat function `delta(stats, activity, facts, dt_ticks, personality) -> Δ`, clamped; personality modulators; charging/sleep/temp/battery inputs.
- Files: dynamics + tests.
- Tests: energy decay per activity; sleep recovery; stress spikes on temp/battery; curiosity on novelty; mood baselines; clamping; determinism (same args ⇒ same δ).
- Acceptance: sim timeline produces monotone-ish believable curves.
- DoD: purity (no I/O, no clock); table of tested scenarios in test names.
- Complexity: M · Deps: C-001, C-003 · Failure: degenerate equilibria → scenario sweeps in M7.

**C-005 — State/stat unit tests consolidated**
- Purpose: full state-layer coverage before decisions.
- Prereq: C-001..C-004.
- Scope: consolidate tests; add property tests (clamps, round-trip, transition validity) for all 4 stats × activities.
- Files: `tests/unit/test_creature_state*.py`.
- Tests: matrix above.
- Acceptance: coverage ≥ 85% on creature/state modules.
- DoD: green; no flaky ordering.
- Complexity: M · Deps: C-001..C-004 · Failure: flaky → pure funcs avoid.

### M4 — Decision Engine (Sprint 5)

**D-001 — Context builder**
- Purpose: observation + facts + memory → decision context.
- Prereq: P-001, M-001 (basic store), C-004.
- Scope: `creature/context.py`: pure `build_context(observation, facts, memory_summary, clock) -> Context`; dedup; memory injection via interface (memory may be empty early).
- Files: context + tests.
- Tests: full context assembly; memory optional/absent.
- Acceptance: decision code reads only Context.
- DoD: Context typed; no adb imports reachable (lint).
- Complexity: M · Deps: P-001, C-004 · Failure: context bloat → freeze schema.

**D-002 — Need evaluation**
- Purpose: context → need deficits.
- Prereq: D-001.
- Scope: `creature/needs.py`: `evaluate_needs(context, stats) -> Needs{energy_demand, curiosity_demand, stress_relief, social?no}`; thresholds data-driven.
- Files: needs + tests.
- Tests: battery 90 vs 15; night; temp high; screen off; empty context.
- Acceptance: needs reflect perception intuitively.
- DoD: pure + table-tested.
- Complexity: S · Deps: D-001 · Failure: threshold tuning → config keys.

**D-003 — Candidate action model + registry**
- Purpose: actions as data, precondition + score-function per action.
- Prereq: D-002, X-001 (interface exists as stub from M5 — **dependency note**: define `ActionSpec` protocol in D-003; concrete executors in M5).
- Scope: `creature/candidates.py`: `ActionSpec{id, level, params_schema, precondition(context, stats) -> bool, utility(context, needs, stats) -> float, cost}`; `registry` seeded with the §I.5 action set (scoring only, no execution).
- Files: candidates module + tests.
- Tests: registry complete; each precondition cases; cost table.
- Acceptance: decision engine sees same candidate set in sim/device.
- DoD: registry registration API; IDs stable.
- Complexity: M · Deps: D-002 · Failure: behavioral drift → score functions versioned.

**D-004 — Utility scoring**
- Purpose: deterministic weighted scores + personality + seeded noise.
- Prereq: D-003, R-006.
- Scope: `creature/scoring.py`: `score(candidate, needs, stats, personality, rng, tick) -> float`; weights per personality (§I.4); noise [-2,2] seeded by (seed, tick, action_id); clamp 0..100.
- Files: scoring + tests.
- Tests: weight effect; personality delta; noise reproducibility; clamp.
- Acceptance: same seed+tick ⇒ identical scores.
- DoD: noise separated (testable toggling noise=0).
- Complexity: M · Deps: D-003, R-006 · Failure: tuning → config personalities.

**D-005 — Deterministic selector**
- Purpose: pick argmax; handle ties; handle empty.
- Prereq: D-004.
- Scope: `creature/selector.py`: `select(candidates) -> Selection{chosen|null, reason}`; tie-break (safety level, then lexical id); empty → `idle` sentinel decision.
- Files: selector + tests.
- Tests: normal, tie, empty, one-blocked.
- Acceptance: selection stable across runs.
- DoD: tie behavior documented; idle path never crashes.
- Complexity: S · Deps: D-004 · Failure: no candidates at all → idle action defined in registry regardless.

**D-006 — Decision record + logging**
- Purpose: full trace (§G.4).
- Prereq: D-005.
- Scope: `creature/decision.py`: `DecisionRecord` assembly (context snapshot, scores, selection, safety, execution placeholder), id scheme `d-<tick>-<hash>`, serialization.
- Files: decision module + tests.
- Tests: record completeness; serialization round-trip.
- Acceptance: `creature decisions --explain` renders (M13).
- DoD: record contains everything `--explain` needs.
- Complexity: S · Deps: D-005 · Failure: record bloat → context stored compactly.

**D-007 — Decision log store**
- Purpose: persist decision history.
- Prereq: D-006.
- Scope: SQLite `decision` table; append; query by id/limit; prune policy (keep last N, e.g. 10k).
- Files: `creature/decision_store.py` + tests.
- Tests: append/query/prune.
- Acceptance: `creature decisions` reads persisted.
- DoD: immutable after write (append-only).
- Complexity: S · Deps: D-006, R-002 · Failure: growth → prune.

**D-008 — Determinism golden tests**
- Purpose: freeze decision behavior.
- Prereq: D-001..D-007.
- Scope: golden files: scripted observation sequences → decision traces; `--update-golden` flag workflow documented.
- Files: `tests/regression/golden/*.json`, runner.
- Tests: same seed/time/inputs ⇒ byte-identical traces.
- Acceptance: engine change breaks goldens visibly.
- DoD: golden update workflow documented; CI-lite runs them.
- Complexity: M · Deps: D-001..D-007 · Failure: golden churn → review process.

### M5 — Creature Actions (Sprint 6)

**X-001 — Action interface + registry + allowlist**
- Purpose: concrete execution layer matching D-003 specs.
- Prereq: D-003.
- Scope: `creature/actions/base.py`: `ActionExecutor` protocol (`execute(params, backend) -> ActionResult`), `ActionRegistry` binding specs↔executors, allowlist config (`enabled_levels`).
- Files: base module + registry + tests.
- Tests: registry binding completeness; allowlist gating.
- Acceptance: decision engine only sees allowed executors.
- DoD: every ActionSpec (M5 set) has executor or explicit `unimplemented` marker (fail loudly in device mode, no-op in sim).
- Complexity: M · Deps: D-003 · Failure: spec/executor drift → registry validation test.

**X-002 — Action backends (real vs sim)**
- Purpose: same action, two targets.
- Prereq: X-001, A-001.
- Scope: `actions/backend.py`: `RealBackend(adb_client)` (bounded command templates, param validation), `SimBackend` (always success + recorded result, configurable failure injection later).
- Files: backends + tests.
- Tests: sim success; template param injection attempts rejected; command built as array.
- Acceptance: swap via one config field.
- DoD: no executor touches adb directly (lint).
- Complexity: M · Deps: X-001, A-001 · Failure: injection → params validated against allowlists (int ranges, pkg ∈ allowed).

**X-003 — Notify action**
- Purpose: creature visible on phone.
- Prereq: X-002.
- Scope: `cmd notification post -S bigtext -t <title> tag creature <text>`; titles limited length; success = exit 0.
- Files: executor + fixtures + tests.
- Tests: normal; too-long text truncated; command failure mapped.
- Acceptance: device shows notification (hw smoke) in S6.
- DoD: text sanitized (no newlines beyond separator).
- Complexity: S · Deps: X-002 · Failure: `cmd notification` absent pre-Android-8 → version-gated fallback.

**X-004 — Vibrate action**
- Purpose: poke.
- Prereq: X-002.
- Scope: `cmd vibrator_manager vibrate <ms>` with fallback `cmd vibrator vibrate <ms>`; param ms 100..2000.
- Files: executor + fixtures + tests.
- Tests: both variants; out-of-range rejected.
- Acceptance: vibration on hw (hw smoke).
- DoD: no infinite vibration; max enforced.
- Complexity: S · Deps: X-002 · Failure: vibrator_manager missing → fallback tested.

**X-005 — Brightness action**
- Purpose: moderate brightness nudges.
- Prereq: X-002.
- Scope: `settings put system screen_brightness <0..255>`; only when screen on; value derivation (e.g., night dim) by spec logic.
- Files: executor + tests.
- Tests: range validation; screen-off precondition blocks; value math.
- Acceptance: brightness changes on hw (hw smoke).
- DoD: writes settings only within params schema bounds.
- Complexity: S · Deps: X-002 · Failure: auto-brightness override → document.

**X-006 — Volume action**
- Purpose: gentle volume changes.
- Prereq: X-002.
- Scope: `media volume --stream 3 --set <0..max>`; max from `media volume --stream 3 --get`.
- Files: executor + tests.
- Tests: parse get; set range; out-of-range.
- Acceptance: volume changes on hw (hw smoke).
- DoD: never mutes to 0 unless spec explicitly (default no).
- Complexity: S · Deps: X-002 · Failure: device max varies → read back before set.

**X-007 — Launch-app action**
- Purpose: curated exploration.
- Prereq: X-002.
- Scope: allowlist map pkg→component in config (`allowed_apps`); `am start -n <component>`; params must be present in allowlist; result via exit code + `am` output parse.
- Files: executor + tests.
- Tests: allowed launch; disallowed pkg blocked at safety; unknown component error mapped.
- Acceptance: creature launches only allowlisted apps.
- DoD: allowlist enforced twice (registry + executor guard).
- Complexity: S · Deps: X-002 · Failure: component vanished → ACTION_FAILED + stress penalty (backoff in scorer? — handled by failure signal in X-009).

**X-008 — Battery-saver toggle (EXPERIMENTAL)**
- Purpose: creature can conserve.
- Prereq: X-002.
- Scope: `settings put global low_power 1` (+ clear); only when `experimental: true` config; version caveats documented.
- Files: executor + tests.
- Tests: disabled by default; enabled path; rollback failure.
- Acceptance: never runs unless flag.
- DoD: default-off; warning logged on enable.
- Complexity: S · Deps: X-002 · Failure: OEM ignores → result checked.

**X-009 — Safety gate enforcement + failure signals**
- Purpose: allowlist is final; failures feed back.
- Prereq: X-001.
- Scope: `creature/safety.py`: pre-execution `blocked?` (level allowed, allowlist, cooldown, healthy connection, not already executing); `attempt` bookkeeping; failure → decision `execution.status=failed` + `recent_failure(pkg/action)` fed to scorer (backoff).
- Files: safety + tests.
- Tests: each block rule; block recorded; failure feedback loop.
- Acceptance: blocked action never executes (assert with spy backend).
- DoD: execution path single choke point.
- Complexity: M · Deps: X-001 · Failure: bypass attempts → registration-time validation.

**X-010 — Cooldowns / rate limits**
- Purpose: no spam.
- Prereq: X-009.
- Scope: per-action cooldown config (`notify: 600s`, `vibrate: 300s`, `launch_app: 120s`…); cooldown checked in safety; sim clock based.
- Files: cooldown module + tests.
- Tests: limits honored; reset after window; per-action independence.
- Acceptance: max N notifications/hour enforced.
- DoD: data-driven table.
- Complexity: S · Deps: X-009 · Failure: clock misuse → injected clock only.

**X-011 — Action test suite (fixtures + failure modes)**
- Purpose: prove actions under failure.
- Prereq: X-003..X-010.
- Scope: fixture-driven execution (A-005 transport): command timeout→failed, exit≠0→failed, missing device→skipped; sim backend parity.
- Files: `tests/adapter/test_actions*.py`.
- Tests: matrix per action.
- Acceptance: full action matrix green without hw.
- DoD: every failure branch covered.
- Complexity: M · Deps: X-003..X-010 · Failure: device-only quirks → hw smoke tests marked.

### M6 — Creature Memory (Sprint 7)

**M-001 — Event store schema**
- Purpose: normalized events (H.2).
- Prereq: R-002.
- Scope: SQLite `event` table schema + migration scaffolding (`user_version`), insert/query API, indexes (ts, type).
- Files: `memory/store.py` + tests.
- Tests: insert/query; index use; migration from v0.
- Acceptance: all producers write here.
- DoD: schema_version column + migration script pattern.
- Complexity: S · Deps: R-002 · Failure: concurrency → single writer (Lab is single-process).

**M-002 — Short-term ring memory**
- Purpose: bounded recent context.
- Prereq: M-001.
- Scope: `memory/short_term.py`: bounded ring (config N=2000) over events; window queries; pruning; determinism (order by (ts,id)).
- Files: Short-term module + tests.
- Tests: cap; pruning; ordering; missing events.
- Acceptance: `creature memory dump` shows bounded list.
- DoD: memory bounded by config.
- Complexity: S · Deps: M-001 · Failure: unbounded growth → enforced cap test.

**M-003 — Importance scoring**
- Purpose: know what matters.
- Prereq: M-001.
- Scope: `memory/importance.py`: base weight per type + deviation boost (e.g., battery vs rolling median); clamp 0..1.
- Files: importance + tests.
- Tests: type weights; deviation boost; clamps; determinism.
- Acceptance: consolidation uses scores.
- DoD: table-driven; boost factors configurable.
- Complexity: S · Deps: M-001 · Failure: importance floods → cap per type per window.

**M-004 — Long-term pattern extraction**
- Purpose: the "boring" knowledge grows.
- Prereq: M-001, M-003.
- Scope: `memory/long_term.py`: `pattern` table CRUD; extractors: sleep_window (night stats per hour), frequent_apps (fg time), battery_pattern (level/time lows), crash_pattern (installed→removed/updated within window), action_affinity.
- Files: long_term + tests.
- Tests: each extractor on synthetic event streams.
- Acceptance: after a scripted day, patterns present.
- DoD: extractors pure over event windows; output schema fixed.
- Complexity: L · Deps: M-001, M-003 · Failure: pattern noise → minimum-count thresholds.

**M-005 — Consolidation job**
- Purpose: short→long on a schedule.
- Prereq: M-002, M-004.
- Scope: `memory/consolidate.py`: run when due (injected clock: every 240 ticks or first night-tick), processes ring delta, updates patterns, prunes, emits MEMORY_CONSOLIDATED; idempotent (high-water mark).
- Files: consolidate + tests.
- Tests: schedule correctness; idempotency; high-water mark.
- Acceptance: long-term stable across restarts.
- DoD: high-water mark persisted.
- Complexity: M · Deps: M-002, M-004 · Failure: double-consolidation → watermark.

**M-006 — Memory query API**
- Purpose: context + CLI read it.
- Prereq: M-005.
- Scope: `memory/api.py`: `top_patterns(k)`, `recent_events(k, types)`, `summary()`, `find_pattern(type,key)`; deterministic ordering.
- Files: api + tests.
- Tests: shapes; ordering; empty DB.
- Acceptance: D-001 consumes this.
- DoD: summary() is the sole CLI-facing shape.
- Complexity: S · Deps: M-005 · Failure: slow queries → indexes.

**M-007 — Memory tests + determinism**
- Purpose: lock behavior.
- Prereq: M-001..M-006.
- Scope: golden memory evolution: same events+clock ⇒ identical patterns; boundary cases.
- Files: `tests/unit/test_memory*.py`, goldens.
- Tests: as above.
- Acceptance: memory deterministic.
- DoD: goldens + update workflow shared with D-008.
- Complexity: M · Deps: M-001..M-006 · Failure: ordering flake → (ts,id) everywhere.

### M7 — Simulation (Sprint 8)

**S-001 — Fake device environment**
- Purpose: Perception Provider for sim.
- Prereq: P-001, R-005, R-006.
- Scope: `simulation/fake_device.py`: implements `PerceptionProvider` protocol producing Observations from state (battery curve, temp, screen, fg) + optional randomness via SeededRng; `SimBackend` reuse (X-002).
- Files: fake_device + tests.
- Tests: curve follow; seeded determinism; terminal states.
- Acceptance: `creature run --sim` ticks.
- DoD: protocol shared with real provider (single interface).
- Complexity: M · Deps: P-001, R-005/006 · Failure: fake/real divergence → protocol contract tests.

**S-002 — Scenario DSL**
- Purpose: scripted timelines as data.
- Prereq: S-001.
- Scope: `simulation/scenarios.py`: YAML?→ JSON scenarios: events at tick offsets (`at 120: battery 60`, `at 300: screen off`); device curve interpolation; assertions blocks (`expect after 500 ticks: activity sleeping`).
- Files: scenarios module + `scenarios/*.json` + tests.
- Tests: parse; interpolation; assertions evaluated.
- Acceptance: `creature simulate --scenario battery-low`.
- DoD: JSON only (no execution in DSL).
- Complexity: L · Deps: S-001 · Failure: DSL creep → keep read-only data format.

**S-003 — Headless sim runner**
- Purpose: batched runs + reports.
- Prereq: S-001, D-00x loop.
- Scope: `simulation/runner.py`: `run_sim(scenario, seed, ticks, clock_speed) -> SimReport{final_state, decision_count, action_summary, events by type}`; progress minimized.
- Files: runner + tests.
- Tests: run completes; report shape; determinism (twice identical).
- Acceptance: `creature simulate` usable.
- DoD: report JSON-serializable.
- Complexity: M · Deps: S-001, D-007 · Failure: slow ticks → config ticks cap.

**S-004 — Preset scenarios**
- Purpose: regression material.
- Prereq: S-002.
- Scope: `scenarios/low-battery.json` (90→5%, expects sleep), `idle-night.json` (screen off 22:00→07:00, expects sleep window learning + night behavior), `heavy-cpu.json` (temp high spikes → stress + rest), `charging-day.json`.
- Files: 4 scenario files + expected-summary docs.
- Tests: each scenario's `expect` block.
- Acceptance: documented behavior emerges.
- DoD: scenarios green without device.
- Complexity: M · Deps: S-002 · Failure: brittle expectations → assert on ranges, not exact ticks.

**S-005 — Simulation test harness + determinism**
- Purpose: sim is the test bed.
- Prereq: S-003, S-004.
- Scope: parametrized runner over presets × seeds (0..4); golden reports.
- Files: `tests/simulation/*.py`, goldens.
- Tests: preset×seed determinism; mutation of seed changes traces.
- Acceptance: decision engine changes caught by golden diff.
- DoD: report goldens included.
- Complexity: M · Deps: S-003, S-004 · Failure: golden churn → explicit update workflow.

**S-006 — Step/replay debug CLI**
- Purpose: human debugging.
- Prereq: S-003.
- Scope: `creature simulate --step` (pause per tick, show context/brief) + `creature decisions --explain` reading sim decision log.
- Files: CLI wiring + tests.
- Tests: step mode control flow.
- Acceptance: a user can follow a scenario tick-by-tick.
- DoD: stepping is stateless re-read, not interactive shell.
- Complexity: M · Deps: S-003, D-006 · Failure: UX rough → keep raw table.

### M8 — Pokédex Inventory (Sprint 9)

**K-001 — Pokedex schema + store**
- Purpose: §J tables.
- Prereq: R-002.
- Scope: `pokedex/store.py`: SQLite DDL (device, package, permission, component, process, snapshot, change), upsert semantics, migration scaffolding.
- Files: store + tests.
- Tests: upsert; schema idempotence; migration.
- Acceptance: collectors persist here.
- DoD: upserts keyed per table PK.
- Complexity: M · Deps: R-002 · Failure: schema drift → versioned DDL.

**K-002 — Identity collector**
- Purpose: §J.device row.
- Prereq: A-004.
- Scope: `pokedex/identity.py`: gather getprop set + RAM/storage totals (dumpsys meminfo / df), build `DeviceIdentity` dataclass; `FINGERPRINT_HASH` = sha256 of canonical JSON.
- Files: identity + tests (fixtures).
- Tests: complete identity; missing props; fingerprint stability (same input ⇒ same hash).
- Acceptance: `pokedex fingerprint` data available.
- DoD: fingerprint hash component order fixed.
- Complexity: M · Deps: A-004 · Failure: prop variance → canonical subset only.

**K-003 — Package inventory collector**
- Purpose: the app list.
- Prereq: A-001, K-001.
- Scope: `pokedex/packages.py`: `pm list packages -f` parse (path=pkg), enrich via `pm path`? (already in -f); `pm list packages -d` for disabled; enabled state derived.
- Files: packages collector + fixtures + tests.
- Tests: normal list; unicode/pkg edge names; query failure.
- Acceptance: `pokedex apps` lists.
- DoD: package set + enabled flags stored.
- Complexity: M · Deps: A-001, K-001 · Failure: package count on device → paginated query not needed (list is one command).

**K-004 — Package detail collector**
- Purpose: version + timestamps per package.
- Prereq: K-003.
- Scope: `pokedex/pkg_detail.py`: per-pkg `dumpsys package <pkg>` parse: versionName, versionCode, firstInstallTime, lastUpdateTime, enabled, codePath; batch with per-pkg timeout; progress; stale-tolerant (app vanished mid-scan → null detail + PARSE_FALLBACK).
- Files: detail collector + fixtures + tests.
- Tests: full detail; partial; vanished app.
- Acceptance: version changes detectable later.
- DoD: per-field null on absence.
- Complexity: L · Deps: K-003 · Failure: slow on 60+ apps → concurrency N=4 adb calls (bounded), timeout per call.

**K-005 — Permission collector**
- Purpose: granted permissions per package.
- Prereq: K-004.
- Scope: `pokedex/permissions.py`: from `dumpsys package <pkg>` (`requested permissions:` / `install permissions:` / `runtime permissions:` granted flags); protect-level metadata optional (where cheap, e.g. from `pm list permissions` cache) — default off.
- Files: permissions + fixtures + tests.
- Tests: runtime/normal granted; none; unavailable.
- Acceptance: `pokedex permissions --pkg X`.
- DoD: granted=bool always present; protect_level nullable.
- Complexity: M · Deps: K-004 · Failure: format churn high → tolerant regex pair.

**K-006 — Components collector**
- Purpose: activities/services/receivers/providers + exported.
- Prereq: K-004.
- Scope: `pokedex/components.py`: parse `dumpsys package <pkg>` sections; exported flag where emitted.
- Files: components + fixtures + tests.
- Tests: each kind; exported true/false/missing.
- Acceptance: `pokedex components --pkg X`.
- DoD: kind enum strict; missing exported → null.
- Complexity: M · Deps: K-004 · Failure: section naming varies → tolerant section scanner.

**K-007 — Parsers & malformed-output tests (batch)**
- Purpose: version tolerance en bloc.
- Prereq: K-003..K-006.
- Scope: consolidated fixture matrix for all K-parsers (Android 10/12/15 samples, truncated, garbage); coverage of null paths.
- Files: `tests/adapter/test_pokedex_parsers*.py`.
- Tests: matrix.
- Acceptance: all parsers degrade to null, never crash.
- DoD: no parser raises below the boundary (ParseError only).
- Complexity: M · Deps: K-003..K-006 · Failure: new Android release → recorded fixture + triage.

**K-008 — CLI wiring (scan/apps/permissions/components)**
- Purpose: user-facing inventory.
- Prereq: K-002..K-007, R-003.
- Scope: `pokedex_cmd.py`: `scan` (run collectors, upsert, summary), `apps/permissions/components` renderers (tables + `--json`); `--full` flag (detail+perms+components vs packages-only).
- Files: CLI module + tests (CLI-level, fixture transport).
- Tests: exit codes; output shapes; `--json` valid.
- Acceptance: `pokedex scan` then `pokedex apps` on fixtures.
- DoD: CLI contract per K.3.
- Complexity: M · Deps: K-002..K-007, R-003 · Failure: wide tables → column truncation rules.

### M9 — Pokédex Runtime (Sprint 10)

**K2-001 — Process collector**
- Purpose: what's running.
- Prereq: A-001, K-001.
- Scope: `pokedex/processes.py`: `ps -A -o PID,NAME` + mapping to packages via `/proc/<pid>/cmdline` careful parse or `dumpsys activity processes`; memory per pid from `ps` RSS where readable — degrade to name-only on restriction.
- Files: collector + fixtures + tests.
- Tests: normal; restricted (empty/SELinux denial) → null rows.
- Acceptance: `pokedex processes`.
- DoD: no root assumption; restricted → documented blank.
- Complexity: M · Deps: A-001, K-001 · Failure: SELinux hides /proc → graceful.

**K2-002 — CPU/RAM runtime totals**
- Purpose: system load.
- Prereq: P-005, P-006 (reuse parsers).
- Scope: runtime snapshots reusing load/memory observers into `observation` store with `source=device`.
- Files: reuse; wiring tests.
- Tests: values land typed.
- Acceptance: `pokedex runtime` shows load/mem.
- DoD: reuse, no new parsers.
- Complexity: S · Deps: P-005, P-006 · Failure: stale first cpu sample → note.

**K2-003 — Foreground runtime monitor**
- Purpose: fg changes over time.
- Prereq: P-004.
- Scope: reuse fg observer; persist per-tick fg rows (`runtime_fg` table: serial, ts, pkg, activity); enable APP_FOREGROUND events.
- Files: wiring + events + tests.
- Tests: transition events emitted.
- Acceptance: history shows app sessions.
- DoD: dedup consecutive same-fg.
- Complexity: S · Deps: P-004 · Failure: fg detection blind spots → null rows.

**K2-004 — Network/battery/temp runtime**
- Purpose: keep environment fresh.
- Prereq: P-002, P-008.
- Scope: reuse observers; persist runtime rows; TEMP_HIGH + BATTERY_LOW events into event store.
- Files: wiring + tests.
- Tests: persistence + events.
- Acceptance: `pokedex runtime --watch` coherent.
- DoD: event wiring single source of truth.
- Complexity: S · Deps: P-002, P-008 · Failure: event dupes → latch.

**K2-005 — Runtime store + CLI**
- Purpose: query runtime history.
- Prereq: K2-001..K2-004.
- Scope: `pokedex/runtime.py` store queries; `pokedex runtime [--watch --interval]`; `--json`.
- Files: runtime CLI + tests.
- Tests: query window; watch loop smoke (2 ticks).
- Acceptance: `pokedex runtime --once`.
- DoD: watch terminates via Ctrl-C cleanly.
- Complexity: M · Deps: K2-001..K2-004, R-003 · Failure: unbounded watch → tick cap flag.

**K2-006 — Runtime tests**
- Purpose: coverage.
- Prereq: K2-005.
- Scope: fixture-based runtime pass; failure injection (device dies mid-watch).
- Files: tests.
- Tests: matrix.
- Acceptance: green without hw.
- DoD: mid-watch failure exits cleanly (exit 3).
- Complexity: S · Deps: K2-005 · Failure: flaky timers → injected clock.

### M10 — Snapshot / Diff (Sprint 11)

**DP-001 — Snapshot model + capture**
- Purpose: point-in-time device anatomy.
- Prereq: K-001, K-005.
- Scope: `pokedex/snapshot.py`: capture = identity+packages(+perms+components when `--full`), bounded window (collect sequential, mark per-section timestamp; stale_fields[] if window exceeded), payload JSON file + row.
- Files: snapshot + tests.
- Tests: full snapshot; stale marking; payload round-trip.
- Acceptance: `pokedex snapshot --name baseline`.
- DoD: snapshot self-describing (schema_version, device, ts per section).
- Complexity: M · Deps: K-001, K-005 · Failure: package churn mid-capture → stale_fields marks affected section.

**DP-002 — Diff engine**
- Purpose: meaningful change detection.
- Prereq: DP-001.
- Scope: `pokedex/diff.py`: pure `diff(base, cur) -> ChangeSet`; keys: pkg presence/version/enabled; permission granted; component exported/kind; device identity/config; ignore volatile (processes, runtime).
- Files: diff + tests.
- Tests: add/remove/update; perm change; component change; no-change empty; version downgrade still detected.
- Acceptance: `pokedex diff a b` output.
- DoD: diff is deterministic (sorted); volatile excluded by design.
- Complexity: L · Deps: DP-001 · Failure: false positives → stable key selection.

**DP-003 — ChangeSet model**
- Purpose: typed changes (§J.change).
- Prereq: DP-002.
- Scope: `pokedex/changeset.py`: `Change{kind, pkg|device, detail_json, importance}`; kinds enum; serialization; merge of two changesets.
- Files: changeset + tests.
- Tests: kinds; merge; format.
- Acceptance: events + history consume it.
- DoD: kind enum frozen v1.
- Complexity: S · Deps: DP-002 · Failure: new kinds → additive only.

**DP-004 — Snapshot/diff CLI**
- Purpose: user commands.
- Prereq: DP-001..DP-003, R-003.
- Scope: `pokedex_cmd`: `snapshot`, `diff A B` (by id or name), list snapshots; renderers + `--json`.
- Files: CLI + tests.
- Tests: CLI flows on synthetic snapshots.
- Acceptance: full flow on fixtures.
- DoD: snapshot ids stable and referencable.
- Complexity: M · Deps: DP-001..DP-003 · Failure: id UX → names alias ids.

**DP-005 — Diff golden tests**
- Purpose: lock diff logic.
- Prereq: DP-002.
- Scope: curated snapshot pairs (incl. app removed + permission revoked combined) with expected ChangeSets; regression.
- Files: `tests/regression/diff/*`.
- Tests: pairs.
- Acceptance: diff behavior frozen.
- DoD: goldens committed.
- Complexity: S · Deps: DP-002 · Failure: behavior change → explicit golden review.

### M11 — Historical Device Model (Sprint 12)

**H-001 — Snapshot history store**
- Purpose: timeline of snapshots.
- Prereq: DP-004.
- Scope: persistence of snapshot rows; `list_snapshots`, retention policy (max N, default 50, keep first+last always).
- Files: history store + tests.
- Tests: retention; ordering.
- Acceptance: `pokedex history` lists.
- DoD: retention data-driven.
- Complexity: S · Deps: DP-004 · Failure: disk growth → retention.

**H-002 — Change-event derivation**
- Purpose: snapshots → events timeline.
- Prereq: DP-002, DP-003, H-001.
- Scope: derive `change` rows from consecutive snapshots; emit typed events (APP_INSTALLED/REMOVED/UPDATED, PERMISSION_CHANGED, COMPONENT_CHANGED, CONFIG_CHANGED) into event store for the creature.
- Files: history derivation + tests (3-snapshot synthetic).
- Tests: timeline correctness; gap snapshots (compare consecutive stored).
- Acceptance: `pokedex history` shows when+what changed.
- DoD: derivation idempotent (re-run no dupes).
- Complexity: M · Deps: DP-002, DP-003, H-001 · Failure: duplicate events → dedup by (kind,pkg,from,to,ts).

**H-003 — Device fingerprint**
- Purpose: stable identity + change alert.
- Prereq: K-002.
- Scope: `pokedex/fingerprint.py`: canonical device JSON + hash; `pokedex fingerprint`; detect fingerprint change across time (CONFIG_CHANGED).
- Files: fingerprint + tests.
- Tests: stability; hash determinism; change detection.
- Acceptance: `pokedex fingerprint --json`.
- DoD: hash components enumerated.
- Complexity: S · Deps: K-002 · Failure: volatile props polluting → allowlist fixed.

**H-004 — Trends / mini-reports**
- Purpose: summaries.
- Prereq: H-002.
- Scope: `pokedex/trends.py`: app install/update counts over windows, permission deltas, config change log; `pokedex history --trends`.
- Files: trends + tests.
- Tests: counts; windows.
- Acceptance: useful summary text.
- DoD: pure aggregation queries.
- Complexity: M · Deps: H-002 · Failure: slow → indexes.

**H-005 — History/fingerprint CLI**
- Purpose: user-facing.
- Prereq: H-001..H-004.
- Scope: consolidate CLI per K.3; `--json`.
- Files: CLI + tests.
- Tests: output shapes.
- Acceptance: full M11 shell usable.
- DoD: CLI stable.
- Complexity: S · Deps: H-001..H-004 · Failure: —.

### M12 — Creature + Pokédex Integration (Sprint 13)

**I-001 — EnvironmentModel bridge**
- Purpose: creature never sees adb text (§J semantic layer).
- Prereq: H-002, D-001.
- Scope: `pokedex/environment.py`: build `EnvironmentModel` from latest identity/inventory/runtime/history (top apps by fg time, allowlisted launchables, recent changes, battery/temp/screen/network); typed dataclass; freshness stamps.
- Files: environment module + tests.
- Tests: assembly; missing data → null fields; typed.
- Acceptance: context builder consumes it.
- DoD: no raw strings in EnvironmentModel except explicit names.
- Complexity: M · Deps: H-002, D-001 · Failure: staleness → freshness stamp consumed by creature (ignore stale).

**I-002 — Perception gateway**
- Purpose: device ticks flow through Pokédex.
- Prereq: I-001, P-010.
- Scope: `integration/perception_gateway.py`: device tick = poll observers → Observation → store → edge events → refresh EnvironmentModel; sim tick = FakeDevice → same path (contract shared).
- Files: gateway + tests.
- Tests: both modes produce identical typed stream shape.
- Acceptance: one code path for both modes.
- DoD: single pipeline (config decides source).
- Complexity: M · Deps: I-001, P-010 · Failure: mode divergence → contract tests.

**I-003 — Creature runtime on real device**
- Purpose: the actual goal works.
- Prereq: I-002, S-003 (runner reuse).
- Scope: `creature run --device <serial>`: supervised loop (connection state machine, adaptive poll, decision each tick, actions through safety+backend, persistence, memory) with graceful shutdown (SIGINT → final state save).
- Files: `creature/loop.py` + integration tests (sim-mode E2E + hw smoke).
- Tests: sim E2E full loop; hw smoke `--once`.
- Acceptance: creature lives on a real phone (demo).
- DoD: crash-safe; disconnect-safe; SIGINT-safe.
- Complexity: L · Deps: I-002, S-003 · Failure: loop complexity → keep loop thin, logic in pure functions.

**I-004 — Action routing via environment + safety**
- Purpose: actions respect learned model.
- Prereq: I-001, X-009.
- Scope: action preconditions can consult EnvironmentModel (e.g., launch_app only if pkg present in inventory); safety consults freshness.
- Files: precondition wiring + tests.
- Tests: unknown-pkg blocked; stale env blocks CONTROl.
- Acceptance: creature never acts on ghost state.
- DoD: freshness check in safety gate.
- Complexity: M · Deps: I-001, X-009 · Failure: stale env → block with reason logged.

**I-005 — End-to-end observability**
- Purpose: explain everything on-device.
- Prereq: I-003, D-006.
- Scope: `creature decisions --explain` over device-run traces; raw observation replayed from store; decision→action result chain.
- Files: explain render + tests.
- Tests: explain over recorded device trace.
- Acceptance: §11 example renderable for a real run.
- DoD: every field of DecisionRecord rendered.
- Complexity: M · Deps: I-003, D-006 · Failure: rendering gaps → contract test.

**I-006 — E2E integration tests**
- Purpose: prove the whole.
- Prereq: I-001..I-005.
- Scope: sim-mode full E2E (device provider = fake, everything else real) + hw smoke suite with graceful skip.
- Files: `tests/integration/*.py`.
- Tests: full pipeline; hw marked.
- Acceptance: `make test` (no hw) exercises full pipeline in sim.
- DoD: hw tests skip cleanly; documented run instructions.
- Complexity: L · Deps: I-001..I-005 · Failure: environment-dependent flakes → hw tags.

### M13 — UI / Visualization (Sprint 14)

**U-001 — CLI rendering**
- Purpose: readable terminal output.
- Prereq: I-003 (data available).
- Scope: `cli/render.py`: plain tables (stdlib, no rich yet), status block, deterministic column widths; `--no-color` safe default.
- Files: renderer + tests (snapshot render).
- Tests: table snapshots; no-terminal-width assumptions.
- Acceptance: `creature status` readable.
- DoD: renders identically in pipes/files.
- Complexity: S · Deps: I-003 · Failure: width → truncation rules.

**U-002 — Decision explain view**
- Purpose: why-did-it-do-that.
- Prereq: U-001.
- Scope: `--explain` full view (observation block, facts, internal, candidates w/ scores, selected, safety, execution, after).
- Files: explain view (move I-005 render here) + tests.
- Tests: golden render.
- Acceptance: §11 example achievable.
- DoD: scores shown w/ reasons.
- Complexity: M · Deps: U-001 · Failure: verbosity → `--brief` flag.

**U-003 — History export (HTML/text)**
- Purpose: shareable story of device+creature.
- Prereq: H-002, D-007.
- Scope: `pokedex history --export report.html` (self-contained file, no assets) + `creature history --export`; text fallback.
- Files: exporter + tests.
- Tests: file valid; stable content.
- Acceptance: export opens offline.
- DoD: single self-contained file.
- Complexity: M · Deps: H-002, D-007 · Failure: escaping → minimal HTML gen.

**U-004 — Watch mode**
- Purpose: live view.
- Prereq: I-002, R-003.
- Scope: `creature run --watch` (live status block, no-clear in pipes) + `pokedex runtime --watch` niceties; tick-rate aware rendering (redraw ≤ 4 Hz).
- Files: watch render + tests.
- Tests: pipe-safe (non-TTY = plain lines).
- Acceptance: live demos.
- DoD: TTY detection, no ANSI when piped.
- Complexity: M · Deps: I-002, R-003 · Failure: TTY games → ANSI only on TTY.

### M14 — Hardening / Documentation (Sprint 15)

**N-001 — Failure-injection suite**
- Purpose: prove resilience under adversity.
- Prereq: I-006.
- Scope: fault injection at transport (timeout, random malformed, mid-command kill), device disconnect mid-scan, reboot (uptime reset → DEVICE_BOOTED), battery NaN; assertions: no crash, correct exit/event, state intact.
- Files: `tests/failure/*.py`.
- Tests: matrix.
- Acceptance: all green.
- DoD: each fault documented with expected behavior.
- Complexity: L · Deps: I-006 · Failure: fault injector itself flaky → deterministic fault schedules.

**N-002 — Soak test (24 h)**
- Purpose: long-run stability.
- Prereq: N-001.
- Scope: `scripts/soak.py`: sim soak (24 h sim-time, fast) + optional hw soak; metrics (decisions, events, memory size, DB size, runtime) asserted within budgets.
- Files: soak script + test.
- Tests: bounded DB growth; no state corruption; determinism of first N decisions.
- Acceptance: soak green.
- DoD: soak report format documented.
- Complexity: L · Deps: N-001 · Failure: invisible leaks → DB size assertions.

**N-003 — Docs: troubleshooting + dev guide**
- Purpose: operability.
- Prereq: M12.
- Scope: `docs/troubleshooting.md` (adb issues, device quirks, permission denials, offline states), `docs/development.md` (setup, test matrix, how to add an action/observer/CLI command), update README quickstart.
- Files: docs.
- Tests: none (link-check in lint).
- Acceptance: a stranger can set up + run.
- DoD: walkthrough executed once.
- Complexity: M · Deps: M12 · Failure: docs rot → README CI check.

**N-004 — Performance budgets + benchmarks**
- Purpose: meet NFR-5.
- Prereq: I-006.
- Scope: benchmark suite: perception tick, CLI cold start, package scan (fixture sizes), diff on 200-pkg sets; budgets asserted (thresholds in config; CI-lite run).
- Files: `tests/bench/*.py`.
- Tests: budgets.
- Acceptance: budgets met on dev machine.
- DoD: budget table documented (machine + measured).
- Complexity: M · Deps: I-006 · Failure: machine variance → relative budgets for scans, absolute for pure functions.

**N-005 — Release/versioning/changelog**
- Purpose: v1.0.0.
- Prereq: N-003.
- Scope: version bump to 1.0.0, `CHANGELOG.md`, packaging polish (`pip install .` from sdist), `creature --version` consistent.
- Files: CHANGELOG.md, pyproject bump.
- Tests: sdist install smoke.
- Acceptance: v1.0.0 tag.
- DoD: changelog lists per-milestone completions.
- Complexity: S · Deps: N-003 · Failure: —.

**N-006 — Security review pass**
- Purpose: allowlist + injection audit.
- Prereq: I-004.
- Scope: systematic review: no shell=True; command arrays everywhere; all params validated; action levels default safe; experimental default off; replay of recorded commands can't execute anything (recordings are read-only). Write findings into `docs/security.md`.
- Files: docs/security.md + any fixes.
- Tests: grep-based lint extension (no `shell=True`, no `os.system`).
- Acceptance: zero findings of severity > info.
- DoD: security doc committed.
- Complexity: M · Deps: I-004 · Failure: finding → fix first (blocker behavior).

### Deferred / optional backlog (not scheduled)
- `X-SND Sound action` (media play) — deferred: device-specific; revisit M14+.
- `K2-007 logcat event stream` (push channel on API 30+ w/ perms caveats) — optional; replaces some polling later.
- `U-005 rich/matplotlib dashboards` — needs a ticket + justification (deps policy 0.10).
- `A-008 WiFi-adb pairing assistant` (`adb pair`) — optional ergonomics.
- `LLM-001 Local analysis layer (llama.cpp)` — advisory explanations on recorded data only; never in decision loop; **deliberately not scheduled**.

---

## P. Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|-----------|--------|-----------|-------|
| P-01 | ADB output variance across Android/OEM versions | High | Med | Tolerant parsers (null-not-fail), recorded fixtures per version, PARSE_FALLBACK tracking, `pokedex record` re-capture | M2/M8 |
| P-02 | adb transport flakiness (USB drop, sleep, server kill) | High | Med | Connection state machine, capped backoff, never-corrupt atomic writes, healthy-gate before actions | M1 |
| P-03 | Device unavailable during development | Certain (none connected now) | Med | Simulator-first (M3–M7 device-free), fixture transport, hw tests skippable | All |
| P-04 | Permission/settings changes blocked by Android policy | Med | Low | No-root baseline; actions degrade to safe; block recorded + surfaced | M5 |
| P-05 | Device sleeps / deep-sleep kills adb | Med | Med | Idle-mode cadence preserves battery; reconnection handles wake; actions gated on healthy connection | M1/M5 |
| P-06 | Creature behavior degenerates (too sleepy / too hyper) | Med | High | Scenario sweeps in M7, stat clamping, hysteresis, golden tests make drift visible | M4/M7 |
| P-07 | Scope creep (LLM, UI shine, on-device app) | High | High | Backlog gates: no LLM in core, deps policy, ADR process, "smaller working system first" | PM |
| P-08 | Snapshot capture races (apps change mid-scan) | Med | Low | bounded capture window + stale_fields marking; diff ignores volatile data | M10 |
| P-09 | Memory/DB unbounded growth | Med | Med | Ring caps, retention policies, prune jobs, soak assertions | M6/M14 |
| P-10 | Python 3.14 rolling-release breakage | Low | Med | stdlib-only, pyproject pins, setup.sh recreates venv, Makefile gates | M0 |
| P-11 | Manual/АРI disintegration: parsers duplicated between perception & pokedex | Med | Med | Single observer modules reused (K2-* reuse P-*), lint for duplicated parsers | M8/M9 |
| P-12 | Golden files become a maintenance burden | Med | Low | Explicit update workflow + review; keep goldens small/focused | M4/M7 |
| P-13 | USB-based dev wears the device battery | Med | Low | Poll cadence config, idle slowdown, soak on sim | M2 |

## Q. Open Questions

Must-resolve-before-implementation is marked; everything else is opportunistic.

1. **Which physical device(s) are the test targets?** (blocking for M8+ tuning, not for M0–M7) — Need model + Android version. Plan assumes nominal Android 10–16; first real device defines fixture baseline. *Action: user provides `adb devices -l` output when convenient.*
2. **USB or network (adb over WiFi) as primary transport?** (not blocking — transport is an AdbClient detail) — USB default; WiFi documented as config option.
3. **Will the device be permanently connected, or is development mostly sim-first with occasional device sessions?** (not blocking) — Affects how often hw smoke runs; assumed "occasional".
4. **Should the creature make audible/visible actions during development** (vibration/notification spam risk on a daily-driver phone)? (not blocking) — Default: SAFE actions on, CONTROL gated by config; a dedicated test device is recommended.
5. **Is a local LLM ("explain like I'm 5" on recorded data) desired at all, eventually?** (not blocking; deliberately unscheduled) — Default: no LLM; revisit post-M14.
6. **Is the target device allowed to sleep normally, or should the lab keep it awake?** (not blocking) — Default: normal sleep; creature reacts to wake/idle rather than preventing sleep (device-battery-respectful).
7. **Device locale/timezone** (not blocking) — Day/night detection assumes device local time via `getprop persist.sys.timezone`; confirm per device.
8. **Should the lab monitor multiple devices concurrently, or is one active device enough for v1?** (not blocking) — Architecture is serial-keyed; concurrent supervision is out of scope for v1 (v1 = one active device, others discoverable).

---

## R. Recommended First Sprint

**Sprint 1 = Milestone M0 — Repository / Architecture** (exact tasks: **R-001 → R-009**).

Objective: a reproducible, tested, dependency-free skeleton with both CLI entry points, config, clock/RNG/error/logging foundations, docs, and a one-command dev loop — **no device, no simulation, no creature logic yet**.

Prereqs: none (empty repo exists). Duration target: 1 focused session for R-001..R-008, 1 for R-009 + demo.

Implementation order is exactly the backlog order: R-001 (git skeleton) → R-002 (package + toolchain + smoke tests) → R-003 (config) → R-004 (logging) → R-005 (clock) → R-006 (RNG) → R-007 (errors) → R-008 (docs/ADRs) → R-009 (Makefile gates).

Exit criteria (all must hold):
- `make setup && make test` green on a clean checkout, **without any device or network**.
- `creature --version` and `pokedex --version` run and exit 0; `creature config validate` exits 0; invalid config exits 5.
- Wall-clock grep gate passes (no `datetime.now()`/`time.time()` outside adapter boundary; config exception documented).
- `docs/PRD.md` + ADR-001..008 committed; repo has a clean first commit.
- Coverage/lint targets defined in Makefile (enforcement of 85% core coverage begins M6; gate defined now).

Expected outputs: skeleton repo, package, tooling, docs, one Makefile.
Tests: `tests/smoke/*` + unit tests for config/logging/clock/rng/errors.
DoD / Done-definition per task: see R-00x blocks above.
After S1: Sprint 2 (M1) begins **only after S1 exit criteria are demonstrated** to the user.

---

## Appendix A — ADB Command Inventory (stability notes)

| Purpose | Command | Stability | Notes |
|---------|---------|-----------|-------|
| Device list | `adb devices -l` | High | serial/model/state; parsing tolerant |
| Props | `adb shell getprop <key>` | High | keys may be absent on OEM |
| Battery | `adb shell dumpsys battery` | Med-High | status codes stable; key labels mostly stable |
| Screen/wake | `adb shell dumpsys power` | Med | `mWakefulness` widely present; key labels vary |
| Foreground | `adb shell dumpsys window windows` / `dumpsys activity activities` | Med | focus lines vary by version — dual strategy |
| CPU | `adb shell dumpsys cpuinfo` | Med | first sample often "TIMEOUT" — tolerate |
| RAM | `adb shell dumpsys meminfo` | Med-High | summary labels vary |
| Storage | `adb shell df -k /data` | High | |
| Network | `adb shell dumpsys connectivity` | Low-Med | verbosity varies — key-line parsing only |
| Uptime | `adb shell cat /proc/uptime` | High | /proc partially restricted on some ROMs → fallback `uptime` |
| Brightness | `adb shell settings get/put system screen_brightness` | Med | auto-brightness may override |
| Volume | `adb shell media volume --stream 3 --get/--set N` | Med | max varies by device |
| Notify | `adb shell cmd notification post …` | Med | present ≥ Android 8 |
| Vibrate | `adb shell cmd vibrator_manager vibrate N` | Med | ≥ Android 12; older variant `cmd vibrator vibrate N` |
| Launch | `adb shell am start -n <component>` | High | component must exist |
| Battery saver | `adb shell settings put global low_power 1` | Low | OEM-dependent — EXPERIMENTAL |
| Packages | `adb shell pm list packages -f` | High | |
| Pkg detail | `adb shell dumpsys package <pkg>` | Med-High | section labels vary by version |
| Processes | `adb shell ps -A -o PID,NAME` | Med | mappings to pkg best-effort |

Rule: every command above is a **static template + validated params**, never string-built from untrusted input (NFR-6).

---

## Appendix B — Microtask index (quick reference)

R-001..R-009 (M0) · A-001..A-007 (M1) · P-001..P-013 (M2) · C-001..C-005 (M3) · D-001..D-008 (M4) · X-001..X-011 (M5) · M-001..M-007 (M6, memory) · S-001..S-006 (M7) · K-001..K-008 (M8) · K2-001..K2-006 (M9) · DP-001..DP-005 (M10) · H-001..H-005 (M11) · I-001..I-006 (M12) · U-001..U-004 (M13) · N-001..N-006 (M14). Deferred: X-SND, K2-007, U-005, A-008, LLM-001. **Total scheduled: 106 microtasks across 15 sprints.**

---

*End of planning package. Implementation begins only after Sprint 1 approval.*