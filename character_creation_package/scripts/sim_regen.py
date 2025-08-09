import time
from pathlib import Path
import sys

# Ensure package root is on sys.path so `character_creation` is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    resources_config_loader,
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
    resource_config = resources_config_loader.load_resource_config(root / "resources_config.yaml")
    formulas = __import__("yaml").safe_load(open(root / "formulas.yaml", "r", encoding="utf-8"))

    hero = create_new_character(
        "Regen_Test",
        stat_tmpl,
        slot_tmpl,
        fields,
        defaults,
        resources,
        progression=progression,
        formulas=formulas,
    )

    hero.hp = 5  # simulate damage
    hero.mana = 2

    print(f"Before regen: HP={hero.hp}, Mana={hero.mana}")
    for i in range(5):
        time.sleep(1)
        hero.regen_tick(resource_config, time.time())
        print(f"[t+{i+1}s] HP={hero.hp:.2f}, Mana={hero.mana:.2f}")


if __name__ == "__main__":
    main()
