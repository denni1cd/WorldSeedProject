import time
from pathlib import Path
import sys
import yaml

# Ensure package root is on sys.path so `character_creation` is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    status_effects_loader,
)
from character_creation.models.factory import create_new_character


def main():
    root = Path(__file__).parents[1] / "character_creation" / "data"
    stat_tmpl = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(root / "slots.yaml")
    fields = appearance_loader.load_appearance_fields(root / "appearance" / "fields.yaml")
    defaults = appearance_loader.load_appearance_defaults(root / "appearance" / "defaults.yaml")
    resources = resources_loader.load_resources(root / "resources.yaml")
    progression = progression_loader.load_progression(root / "progression.yaml")
    effects = status_effects_loader.load_status_effects(root / "status_effects.yaml")
    formulas = yaml.safe_load(open(root / "formulas.yaml", "r", encoding="utf-8"))

    hero = create_new_character(
        "Effect_Test",
        stat_tmpl,
        slot_tmpl,
        fields,
        defaults,
        resources,
        progression=progression,
        formulas=formulas,
    )

    hero.apply_status_effect("poison", effects["poison"], time.time())
    hero.apply_status_effect("bless", effects["bless"], time.time())

    for i in range(12):
        hero.update_status_effects(time.time())
        charm_val = (
            hero.get_effective_stat("CHA")
            if hasattr(hero, "get_effective_stat")
            else hero.stats.get("CHA", 0)
        )
        print(
            f"[t+{i}s] HP={hero.hp:.2f}, Charm={charm_val:.2f}, Effects={len(hero.active_effects)}"
        )
        time.sleep(1)


if __name__ == "__main__":
    main()
