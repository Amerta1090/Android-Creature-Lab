#!/usr/bin/env python3
"""Source hygiene lint (PRD R-009 `make lint` helper).

Checks, on top of ``python -m compileall``:

1. **Banned wall-clock / randomness tokens** absent from ``src/``
   (PRD NFR-2 / R-005/R-006 DoD, ADR-005): ``datetime.now``, ``time.time``,
   and module-level ``random`` API calls (token ``random.``).
2. **Import surface** — stdlib-only + project-only: every import in ``src/``
   must resolve to the standard library or the ``android_creature`` package
   ("nothing exotic", PRD §0.10), and stdlib imports must precede project
   imports within each file (clean grouping).

Exits 0 when clean, 1 listing each violation. Intentionally AST-based for
imports (no execution) and plain-text for token checks.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
PACKAGE = "android_creature"

BANNED_TOKENS = ("datetime.now", "time.time", "random.")


def _source_files() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


def check_tokens() -> list[str]:
    issues: list[str] = []
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        for token in BANNED_TOKENS:
            if token in text:
                rel = path.relative_to(SRC.parent)
                issues.append(f"{rel}: banned token {token!r}")
    return issues


def check_imports() -> list[str]:
    issues: list[str] = []
    stdlib = frozenset(sys.stdlib_module_names)
    for path in _source_files():
        rel = path.relative_to(SRC.parent).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:  # compileall already flags this; be lenient
            issues.append(f"{rel}: cannot parse: {exc}")
            continue
        seen_project = False
        for node in tree.body:
            for imp in _imports_of(node):
                module = _module_name(imp)
                if module is None:
                    continue  # relative/local import (`from . import …`)
                if module == PACKAGE or module.startswith(PACKAGE + "."):
                    seen_project = True
                    continue
                if module in stdlib:
                    if seen_project:
                        issues.append(
                            f"{rel}:{imp.lineno}: stdlib import {module!r} "
                            "after a project import — group stdlib first"
                        )
                    continue
                issues.append(
                    f"{rel}:{imp.lineno}: non-stdlib/non-project import {module!r}"
                )
    return issues


def _imports_of(node: ast.stmt) -> list[ast.Import | ast.ImportFrom]:
    out: list[ast.Import | ast.ImportFrom] = []
    if isinstance(node, ast.Import):
        out.append(node)
    elif isinstance(node, ast.ImportFrom) and node.level == 0:
        out.append(node)
    return out


def _module_name(imp: ast.Import | ast.ImportFrom) -> str | None:
    if isinstance(imp, ast.Import):
        return imp.names[0].name.split(".")[0]
    return imp.module  # may be None for `from . import x` (level > 0 handled)


def main() -> int:
    issues = check_tokens() + check_imports()
    if issues:
        print("src hygiene violations:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("src hygiene: OK (no banned tokens, stdlib-only imports)")
    return 0


if __name__ == "__main__":
    sys.exit(main())