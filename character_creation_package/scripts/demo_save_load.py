from pathlib import Path
import yaml

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
)
from character_creation.models.factory import create_new_character


def main() -> None:
    root = Path(__file__).parents[1] / "character_creation" / "data"
    stat_tmpl = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(root / "slots.yaml")
    fields = appearance_loader.load_appearance_fields(root / "appearance" / "fields.yaml")
    defaults = appearance_loader.load_appearance_defaults(root / "appearance" / "defaults.yaml")
    resources = resources_loader.load_resources(root / "resources.yaml")
    progression = progression_loader.load_progression(root / "progression.yaml")
    formulas = yaml.safe_load(open(root / "formulas.yaml", "r", encoding="utf-8"))

    hero = create_new_character(
        "SaverHero",
        stat_tmpl,
        slot_tmpl,
        fields,
        defaults,
        resources,
        progression=progression,
        formulas=formulas,
    )
    save_path = Path("saves/saverhero.yaml")

    hero.save(save_path)
    print(f"Saved character to {save_path}")

    loaded_hero = hero.load(save_path)
    print(f"Loaded hero: {loaded_hero.name}, HP={loaded_hero.hp}, Mana={loaded_hero.mana}")


if __name__ == "__main__":
    main()
