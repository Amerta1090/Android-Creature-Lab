"""`android_creature.cli` — console entry point package (R-002).

Empty by design: the two gate bodies (`creature`, `pokedex`) live in
`android_creature.cli.main` and are bound via `[project.scripts]` in
`pyproject.toml`. This ``__init__`` exists only so setuptools' static package
discovery (`[tool.setuptools.packages.find]`) picks up ``cli`` as a real
package — without it, ``pip install -e .`` would silently install an entry
point that cannot import, failing the R-002 DoD gate.
"""
