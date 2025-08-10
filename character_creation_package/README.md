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

## Content Packs

You can extend the base catalogs (classes, traits, races, items, and appearance tables) via Content Packs without changing any code.

- Config file: `character_creation/data/content_packs.yaml`

  Example:

  ```yaml
  enabled:
    - starter_pack
  merge:
    on_conflict: "skip"  # one of: "skip" | "override" | "error"
  ```

- To add or enable a pack:
  - Place the pack under `character_creation/data/content_packs/<pack_name>/`
  - Reference it under `enabled:` in `content_packs.yaml`

- Supported files inside a pack (all optional):
  - `classes.yaml` (list or {classes: [...]})
  - `traits.yaml` ({traits: {...}} or direct mapping)
  - `races.yaml` (list or {races: [...]})
  - `items.yaml` (list or {items: [...]})
  - `appearance/tables/*.yaml` (list or {values: [...]})

- Merge policies:
  - **skip**: keep base entry when ids collide
  - **override**: replace base entry with pack's
  - **error**: raise on id collision

- Validation and tooling:
  - Validate data: `python scripts/validate_data.py`
  - List enabled packs and counts: `python scripts/list_content_packs.py`

The CLI and TUI automatically load and merge enabled packs at startup; newly added classes and races will appear in selection lists, and appearance enums are unioned with pack-provided values.

## Live Reload (dev)

- Run `python scripts/dev_watch.py` to watch `character_creation/data/` and re-validate on changes.
- Set `dev.live_reload: true` in `character_creation/data/dev_config.yaml` to auto-reload in the TUI.

## Difficulty & Balance

Gameplay balance is data-driven via `character_creation/data/difficulty.yaml`.

Knobs per difficulty profile:

- hp_scale: scales maximum HP
- mana_scale: scales maximum Mana
- regen_amount_scale: multiplies per-tick regeneration amounts
- status_effect_scale: scales magnitudes of status-effect tick damage/buffs
- xp_gain_scale: scales XP amounts granted to the character
- xp_cost_scale: scales XP required to reach the next level

Usage:

- Set `balance.current` to one of the names under `balance.difficulties`.
- CLI/TUI and scripts can pass an optional `balance` profile to character methods to apply scaling without breaking existing flows.
- Tuning requires no code changes; edit `difficulty.yaml` and re-run.

Example snippet:

```yaml
balance:
  current: easy
  difficulties:
    easy:
      hp_scale: 1.15
      mana_scale: 1.15
      regen_amount_scale: 1.25
      status_effect_scale: 0.85
      xp_gain_scale: 1.10
      xp_cost_scale: 0.90
```

Effects:

- Easy: more HP/Mana, faster regen, weaker negative effects, faster leveling.
- Hard/Nightmare: less HP/Mana, slower regen, stronger effects, slower leveling.
