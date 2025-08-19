import sys
from pathlib import Path


def main():
    # Ensure we can import the package when running as a script
    package_root = Path(__file__).parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    # Deferred imports to avoid E402 and allow dynamic sys.path adjustment
    from character_creation.loaders import (
        stats_loader,
        slots_loader,
        appearance_loader,
        resources_loader,
        progression_loader,
    )
    from character_creation.models.factory import create_new_character
    from character_creation.loaders import difficulty_loader
    from character_creation.services.balance import current_profile

    # quick and dirty: grant XP to a fresh hero and print level/HP/Mana
    root = package_root / "character_creation" / "data"
    stat_tmpl = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(root / "slots.yaml")
    fields = appearance_loader.load_appearance_fields(
        root / "appearance" / "fields.yaml"
    )
    defaults = appearance_loader.load_appearance_defaults(
        root / "appearance" / "defaults.yaml"
    )
    resources = resources_loader.load_resources(root / "resources.yaml")
    progression = progression_loader.load_progression(root / "progression.yaml")
    formulas = __import__("yaml").safe_load(
        open(root / "formulas.yaml", "r", encoding="utf-8")
    )  # quick load

    hero = create_new_character(
        "XP_Test",
        stat_tmpl,
        slot_tmpl,
        fields,
        defaults,
        resources,
        progression=progression,
        formulas=formulas,
    )

    amount = 250  # tweak
    # Difficulty profile
    balance_cfg = difficulty_loader.load_difficulty(root / "difficulty.yaml")
    prof = current_profile(balance_cfg)
    gained = hero.add_general_xp(amount, formulas, stat_tmpl, progression, balance=prof)
    print(
        f"Gained levels: {gained}, level={hero.level}, HP={hero.hp}, Mana={hero.mana}, stat_points={hero.stat_points}"
    )


if __name__ == "__main__":
    main()
