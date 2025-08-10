# WorldSeed Character Creation

## Overview
A data-driven character creation module for an RPG/management game. Content is defined in YAML (stats, classes, traits, appearance, items, formulas), with tested Python models and a CLI/TUI.

## Quick Start
```bash
pip install -e .[dev]
pre-commit install
pytest -q
```

Run the textual TUI:

```bash
python scripts/run_tui.py
```

Run the CLI wizard:

```bash
python scripts/create_character.py
```

Validate all game data quickly:

```bash
python scripts/validate_data.py
```

If validation passes you will see `OK`. A non-zero exit indicates validation failures.

## Notes
Character creation includes Race and Appearance steps in both the CLI (`worldseed-wizard`) and TUI (`worldseed-tui`).

Trait limits are configurable via `character_creation/data/creation_limits.yaml`:

```yaml
limits:
  traits_max: 2
  edit_numeric_step: 0.5
```

Both the CLI and TUI enforce `traits_max` during selection.
