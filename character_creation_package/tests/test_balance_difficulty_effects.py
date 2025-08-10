import pathlib
import yaml
import time
import pytest
from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    difficulty_loader,
)
from character_creation.models.factory import create_new_character
from character_creation.services.balance import current_profile


@pytest.fixture
def base():
    # Resolve data dir relative to this test file so it works from any CWD
    root = pathlib.Path(__file__).resolve().parents[1] / "character_creation" / "data"
    return {
        "stats": stats_loader.load_stat_template(root / "stats" / "stats.yaml"),
        "slots": slots_loader.load_slot_template(root / "slots.yaml"),
        "fields": appearance_loader.load_appearance_fields(root / "appearance" / "fields.yaml"),
        "defaults": appearance_loader.load_appearance_defaults(
            root / "appearance" / "defaults.yaml"
        ),
        "resources": resources_loader.load_resources(root / "resources.yaml"),
        "progression": progression_loader.load_progression(root / "progression.yaml"),
        "formulas": yaml.safe_load(open(root / "formulas.yaml", "r", encoding="utf-8")),
        "balance_cfg": difficulty_loader.load_difficulty(root / "difficulty.yaml"),
    }


def test_hp_mana_scale(base):
    prof_easy = dict(
        current_profile({"current": "easy", "difficulties": base["balance_cfg"]["difficulties"]})
    )
    prof_hard = dict(
        current_profile({"current": "hard", "difficulties": base["balance_cfg"]["difficulties"]})
    )
    hero = create_new_character(
        "Bal",
        base["stats"],
        base["slots"],
        base["fields"],
        base["defaults"],
        base["resources"],
        progression=base["progression"],
        formulas=base["formulas"],
    )
    hero.refresh_derived(base["formulas"], base["stats"], keep_percent=False, balance=prof_easy)
    hp_easy = hero.hp
    mana_easy = hero.mana
    hero.refresh_derived(base["formulas"], base["stats"], keep_percent=False, balance=prof_hard)
    assert hero.hp < hp_easy
    assert hero.mana < mana_easy


def test_regen_scale(base, monkeypatch):
    prof = dict(
        current_profile({"current": "easy", "difficulties": base["balance_cfg"]["difficulties"]})
    )
    hero = create_new_character(
        "Regen",
        base["stats"],
        base["slots"],
        base["fields"],
        base["defaults"],
        base["resources"],
        progression=base["progression"],
        formulas=base["formulas"],
    )
    hero.hp = 0
    now = time.time()
    # simulate a tick due; assume intervals exist
    rcfg = {"regen_intervals": {"hp": 0}, "regen_amounts": {"hp": 1.0}, "regen_caps": {"hp": "max"}}
    hero.regen_tick(rcfg, now, balance=prof)
    assert hero.hp >= 1.0 * prof.get("regen_amount_scale", 1.0) - 1e-6


def test_status_effect_scale(base):
    prof_harder = dict(
        current_profile(
            {"current": "nightmare", "difficulties": base["balance_cfg"]["difficulties"]}
        )
    )
    hero = create_new_character(
        "SE",
        base["stats"],
        base["slots"],
        base["fields"],
        base["defaults"],
        base["resources"],
        progression=base["progression"],
        formulas=base["formulas"],
    )
    hero.hp = 10
    before = hero.hp
    dmg = 1.0 * prof_harder.get("status_effect_scale", 1.0)
    hero.hp -= dmg
    assert hero.hp == pytest.approx(before - dmg, 1e-6)


def test_xp_gain_and_cost(base):
    prof = dict(
        current_profile({"current": "easy", "difficulties": base["balance_cfg"]["difficulties"]})
    )
    hero = create_new_character(
        "XP",
        base["stats"],
        base["slots"],
        base["fields"],
        base["defaults"],
        base["resources"],
        progression=base["progression"],
        formulas=base["formulas"],
    )
    cost_easy = hero.xp_to_next_level(base["formulas"], balance=prof)
    cost_norm = hero.xp_to_next_level(base["formulas"], balance=None)
    assert cost_easy < cost_norm
    hero.xp_total = 0
    gained = hero.add_general_xp(
        200.0, base["formulas"], base["stats"], base["progression"], balance=prof
    )
    assert gained >= 0
