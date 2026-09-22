#!/usr/bin/env python3
"""Generate docs/sprints/sprint-*.md, docs/backlog.md, docs/sprints/README.md from docs/PRD.md.

Rules:
- Parse PRD section O (### Mnn — name (Sprint n)) for task bullets `**ID — Title**`.
- Sprint files get objective/entry/exit criteria from the METADATA dict below (mirrors PRD sections M/N).
- Re-running this script preserves [x] checkboxes found in existing sprint files.
- It is NOT meant to be re-run casually: document in sprints README.
"""
import re
import pathlib

ROOT = pathlib.Path("/home/amerta/Android Creature Lab")
PRD = ROOT / "docs/PRD.md"
SPRINTS_DIR = ROOT / "docs/sprints"

MIL = re.compile(r"^### (?P<mid>M\d+) — (?P<name>.+?) \((?P<sn>Sprint \d+)\)$")
TASK = re.compile(r"^\*\*(?P<id>[A-Z]{1,2}\d*-\d+) — (?P<title>[^*]+)\*\*")
CHECK = re.compile(r"^\- \[(x| )\] (?P<id>[A-Z]{1,2}\d*-\d+)")

# sprint number -> (milestone id, milestone name, objective, entry criteria, [exit criteria])
METADATA = {
    1: ("M0", "Repository / Architecture",
        "Repositori skeleton, package Python, toolchain, config, logging, clock, RNG, errors, docs/ADR, Makefile.",
        "Repo kosong tersedia (hanya dokumen). PRD + status sudah ada.",
        ["make setup && make test hijau tanpa device & tanpa network",
         "creature --version / pokedex --version exit 0; creature config validate exit 0; konfig invalid exit 5",
         "Grep gate wall-clock lolos (tidak ada datetime.now()/time.time() di luar boundary adapter)",
         "docs/PRD.md + ADR-001..008 ter-commit; commit pertama bersih",
         "Gate lint/coverage terdefinisi di Makefile (enforcement 85% mulai M6)"]),
    2: ("M1", "Android Connection Layer",
        "AdbClient, discovery, connection state machine, getprop, fixture transport, fault tests.",
        "M0 selesai.",
        ["Test adapter hijau offline (fixture transport, tanpa adb)",
         "State machine menangani connect/disconnect (test)",
         "Discovery mendukung multi-device by serial"]),
    3: ("M2", "Device Perception",
        "Observation schema, observer (battery/screen/fg/cpu/mem/storage/net/uptime), scheduler adaptif, edge detection, observation store, E2E test.",
        "M1 selesai.",
        ["creature observe menampilkan Observation lengkap di mode sim + fixture",
         "Semua observer punya parser test + UNKNOWN fallback",
         "Edge events (BATTERY_LOW, SCREEN_ON, dll) teruji"]),
    4: ("M3", "Creature State",
        "CreatureState schema, persistence atomik, activity state machine (guarded+hysteresis), stat dynamics registry, test konsolidasi.",
        "M0 selesai.",
        ["State round-trip + clamp teruji",
         "Transisi activity guarded + hysteresis",
         "Coverage >= 85% di modul state"]),
    5: ("M4", "Decision Engine",
        "Context builder, need evaluation, candidate registry, utility scoring, deterministic selector, decision record/store, golden tests.",
        "M3 selesai.",
        ["Input sama => decision sama (golden test)",
         "Tie-break & empty-candidate terdefinisi & teruji",
         "DecisionRecord serializable (replayable)"]),
    6: ("M5", "Creature Actions",
        "Action interface/registry/allowlist, backends real+sim, aksi (notify/vibrate/brightness/volume/launch/battery-saver), safety gate, cooldown, test suite.",
        "M1 + M4 selesai.",
        ["Aksi yang di-block TIDAK PERNAH dieksekusi (test spy backend)",
         "Semua aksi punya fixture test + failure branches",
         "Cooldown/rate limit teruji"]),
    7: ("M6", "Creature Memory",
        "Event store, short-term ring, importance scoring, long-term patterns, consolidation, query API, test determinisme.",
        "M4 selesai.",
        ["Pattern terbentuk dari event scripted; hasil deterministik",
         "Consolidation idempotent (watermark)",
         "Query API deterministik (ordering (ts,id))"]),
    8: ("M7", "Simulation",
        "Fake device, scenario DSL, headless runner, preset scenarios, determinism harness, step/replay CLI.",
        "M4 + M6 selesai.",
        ["Scenario battery-low berperilaku sesuai spec (sleep terpilih)",
         "Determinism: seed sama => trace sama (golden reports)",
         "Semua preset green tanpa device"]),
    9: ("M8", "Pokédex Inventory",
        "Pokedex store, identity, package inventory, package detail, permissions, components, batch parser tests, CLI.",
        "M1 selesai.",
        ["pokedex scan mengisi DB dari fixtures",
         "Semua parser null-tolerant (tidak pernah crash)",
         "pokedex apps/permissions/components berjalan (fixture + hw)"]),
    10: ("M9", "Pokédex Runtime",
        "Process collector, CPU/RAM reuse, foreground monitor, battery/temp/network runtime, runtime store + CLI.",
        "M1 + M8 selesai.",
        ["pokedex runtime --once bekerja di fixtures/hw",
         "Device mati di tengah watch => exit bersih (exit 3)",
         "Events wiring tanpa duplikasi"]),
    11: ("M10", "Snapshot / Diff",
        "Snapshot model+capture, diff engine, ChangeSet model, CLI, diff golden tests.",
        "M8 + M9 selesai.",
        ["pokedex diff a b benar pada curated pairs",
         "Data volatile (process/runtime) dikeluarkan dari diff",
         "Goldens committed"]),
    12: ("M11", "Historical Device Model",
        "History store, change-event derivation, device fingerprint, trends, CLI.",
        "M10 selesai.",
        ["Timeline benar setelah 3 snapshot sintetis",
         "Derivation idempotent (tidak ada duplikasi)",
         "Fingerprint stabil + hash deterministik"]),
    13: ("M12", "Creature + Pokédex Integration",
        "EnvironmentModel bridge, perception gateway, creature run on device, action routing via environment, observability, E2E tests.",
        "M7 + M11 selesai.",
        ["Creature mengonsumsi EnvironmentModel (bukan raw adb)",
         "Sim E2E full pipeline green tanpa hw",
         "hw smoke (run --once) jalan di device nyata"]),
    14: ("M13", "UI / Visualization",
        "CLI rendering, decision explain view, history export (HTML/text), watch mode.",
        "M7 selesai.",
        ["Decision explain view sesuai contoh PRD §11",
         "Export HTML self-contained (bisa dibuka offline)",
         "Watch pipe-safe (tanpa ANSI saat bukan TTY)"]),
    15: ("M14", "Hardening / Documentation",
        "Failure injection, soak 24h, docs (troubleshooting/dev), benchmarks, release v1.0.0, security review.",
        "M12 selesai.",
        ["Soak 24h green (DB/state bounded)",
         "Failure-injection matrix hijau",
         "Tag v1.0.0 + CHANGELOG + docs lengkap"]),
}

DEFERRED = [
    "X-SND — Sound action (media play)",
    "K2-007 — logcat event stream (opsional push channel)",
    "U-005 — rich/matplotlib dashboards (butuh ticket + justifikasi, PRD §0.10)",
    "A-008 — WiFi-adb pairing assistant",
    "LLM-001 — Local analysis layer (konsultatif pada data terekam saja; TIDAK dijadwalkan)",
]


def parse_prd():
    sections = []
    cur = None
    for line in PRD.read_text().splitlines():
        m = MIL.match(line)
        if m:
            cur = {"sn": int(m.group("sn").split()[1]), "mid": m.group("mid"),
                   "name": m.group("name"), "tasks": []}
            sections.append(cur)
            continue
        # stop at deferred/appendix
        if line.startswith("### Deferred") or line.startswith("## "):
            if cur is not None and line.startswith("## "):
                cur = None
            continue
        if cur is None:
            continue
        t = TASK.match(line)
        if t:
            cur["tasks"].append((t.group("id"), t.group("title")))
    return sections


def existing_checked(sprint_file: pathlib.Path):
    if not sprint_file.exists():
        return set()
    return {m.group("id") for m in CHECK.finditer(sprint_file.read_text())}


def render_sprint(sn, sec, checked):
    mid, name, obj, entry, exits = METADATA[sn]
    status = "COMPLETE" if len(checked) == len(sec["tasks"]) and sec["tasks"] else "IN PROGRESS" if checked else "NOT STARTED"
    lines = [
        f"# Sprint {sn:02d} — {mid}: {name}",
        "",
        f"- Status: `{status}`",
        f"- Objective: {obj}",
        f"- Entry criteria: {entry}",
        f"- Spec task: `docs/PRD.md` §O ({mid}) · Checklist master: `docs/backlog.md`",
        "",
        "## Tasks",
        "",
    ]
    for tid, title in sec["tasks"]:
        mark = "x" if tid in checked else " "
        lines.append(f"- [{mark}] **{tid} — {title}**")
    lines += [
        "",
        "## Exit criteria (SEMUA harus terpenuhi sebelum sprint ditandai COMPLETE)",
        "",
    ]
    lines += [f"- [ ] {e}" for e in exits]
    lines += [
        "",
        "## Catatan sesi / keputusan sprint ini",
        "",
        "- (diisi oleh agent setiap sesi)",
        "",
    ]
    return "\n".join(lines)


def render_backlog(sections, total):
    lines = [
        "# Microtask Backlog — Master Checklist",
        "",
        f"> Dibuat otomatis dari `docs/PRD.md` §O · Total task terjadwal: **{total}** · Update: centang DI SINI dan di sprint file saat task selesai.",
        "",
    ]
    for sec in sections:
        mid, name, *_ = METADATA[sec["sn"]]
        lines.append(f"## Sprint {sec['sn']:02d} — {mid}: {name}")
        for tid, title in sec["tasks"]:
            lines.append(f"- [ ] {tid} — {title}")
        lines.append("")
    lines.append("## Deferred (tidak terjadwal, butuh persetujuan user)")
    for d in DEFERRED:
        lines.append(f"- [ ] {d}")
    return "\n".join(lines)


def render_index(sections):
    lines = [
        "# Sprint Index",
        "",
        "> Sprint file adalah pelacak state per sprint. Spec task selalu di `docs/PRD.md` §O. Status global ada di `docs/status.md`.",
        "",
        "| Sprint | Milestone | Status | Tasks | File |",
        "|--------|-----------|--------|-------|------|",
    ]
    for sec in sections:
        sn, mid, name = sec["sn"], sec["mid"], sec["name"]
        f = SPRINTS_DIR / f"sprint-{sn:02d}-{mid.lower()}.md"
        status = "COMPLETE" if f.exists() and "COMPLETE" in f.read_text() else "NOT STARTED"
        lines.append(f"| {sn:02d} | {mid} — {name} | {status} | {len(sec['tasks'])} | `sprint-{sn:02d}-{mid.lower()}.md` |")
    lines += [
        "",
        "## Catatan regenerasi",
        "",
        "File sprint + backlog dihasilkan dari `docs/PRD.md` §O oleh `scripts/gen_sprints.py` (checkbox yang sudah [x] dipertahankan).",
        "Jangan edit struktur task di sprint file — edit PRD §O dulu kalau backlog berubah.",
        "",
    ]
    return "\n".join(lines)


def main():
    sections = parse_prd()
    assert len(sections) == 15, f"expected 15 milestone sections, got {len(sections)}"
    total = sum(len(s["tasks"]) for s in sections)
    SPRINTS_DIR.mkdir(parents=True, exist_ok=True)
    for sec in sections:
        sn = sec["sn"]
        f = SPRINTS_DIR / f"sprint-{sn:02d}-{sec['mid'].lower()}.md"
        checked = existing_checked(f)
        f.write_text(render_sprint(sn, sec, checked))
    (ROOT / "docs/backlog.md").write_text(render_backlog(sections, total))
    (SPRINTS_DIR / "README.md").write_text(render_index(sections))
    print(f"OK: {len(sections)} sprints, {total} tasks -> {SPRINTS_DIR}")


if __name__ == "__main__":
    main()