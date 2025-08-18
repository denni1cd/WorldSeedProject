from pathlib import Path

import pytest

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from character_creation.ui.textual import state


DATA_ROOT = Path(__file__).parents[2] / "character_creation_package" / "character_creation" / "data"
CHAR = DATA_ROOT / "character"
BACK = DATA_ROOT / "backend"


def pick(*candidates: Path) -> Path:
    for p in candidates:
        try:
            if p.exists():
                return p
        except Exception:
            continue
    return candidates[-1]


@pytest.fixture
def hero():
    stat_tmpl = stats_loader.load_stat_template(
        pick(CHAR / "stats" / "stats.yaml", DATA_ROOT / "stats" / "stats.yaml")
    )
    slot_tmpl = slots_loader.load_slot_template(pick(BACK / "slots.yaml", DATA_ROOT / "slots.yaml"))
    fields = appearance_loader.load_appearance_fields(
        pick(CHAR / "appearance" / "fields.yaml", DATA_ROOT / "appearance" / "fields.yaml")
    )
    defaults = appearance_loader.load_appearance_defaults(
        pick(CHAR / "appearance" / "defaults.yaml", DATA_ROOT / "appearance" / "defaults.yaml")
    )
    resources = resources_loader.load_resources(DATA_ROOT / "resources.yaml")
    return state.create_new_character("PeekHero", stat_tmpl, slot_tmpl, fields, defaults, resources)


def test_apply_appearance_and_summarize(hero):
    selection = {"eye_color": "blue", "height_cm": 170}
    state.apply_appearance_selection(hero, selection)
    assert hero.appearance.get("eye_color") == "blue"
    assert hero.appearance.get("height_cm") == 170

    # Build minimal catalogs for summary
    class_catalog = {"classes": [{"id": "fighter", "name": "Fighter"}]}
    trait_catalog = {"traits": {}}

    sel = state.CreationSelections(name=hero.name, class_index=0, trait_ids=[])
    preview = state.build_character_from_selections(
        sel,
        {k: {"initial": v} for k, v in hero.stats.items()}
        or stats_loader.load_stat_template(
            pick(CHAR / "stats" / "stats.yaml", DATA_ROOT / "stats" / "stats.yaml")
        ),
        {"slots": {"hand_main": None}},
        {
            "fields": {
                k: {"default": v if not isinstance(v, (int, float)) else float(v), "type": "any"}
                for k, v in hero.appearance.items()
            }
        },
        {},
        resources_loader.load_resources(
            pick(BACK / "resources.yaml", DATA_ROOT / "resources.yaml")
        ),
        class_catalog,
        trait_catalog,
        {"races": [{"id": "human", "name": "Human"}]},
    )
    summary = state.summarize_character(
        preview,
        [class_catalog["classes"][0]],
        0,
        trait_catalog,
        {"races": [{"id": "human", "name": "Human"}]},
    )
    peek = summary.get("appearance_peek", {})
    assert peek.get("eye_color") == "blue"
    assert "height_cm" in peek
