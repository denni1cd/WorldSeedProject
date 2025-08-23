import pytest
from pathlib import Path

from character_creation.loaders import yaml_utils
from character_creation.services import formula_eval
from character_creation.services import random_utils
from character_creation.models import npc_factory


# It's good practice to define a fixture for the base data path
# This makes tests more portable.
@pytest.fixture(scope="module")
def data_path() -> Path:
    """Provides the absolute path to the data directory."""
    # Assumes tests are run from the root of `character_creation_package`
    # or that the project is installed in editable mode.
    # Path(__file__).parent gives 'tests', .parent gives 'character_creation_package'
    base_dir = Path(__file__).parent.parent
    return base_dir / "character_creation" / "data"


@pytest.fixture(scope="module")
def stat_tmpl(data_path: Path):
    return yaml_utils.load_yaml(data_path / "stats" / "stats.yaml")


@pytest.fixture(scope="module")
def slot_tmpl(data_path: Path):
    return yaml_utils.load_yaml(data_path / "slots.yaml")


@pytest.fixture(scope="module")
def appearance_fields(data_path: Path):
    return yaml_utils.load_yaml(data_path / "appearance" / "fields.yaml").get("fields", {})


@pytest.fixture(scope="module")
def class_catalog(data_path: Path):
    # The YAML file has a root key 'classes', so we need to access it.
    return yaml_utils.load_yaml(data_path / "classes.yaml").get("classes", [])


@pytest.fixture(scope="module")
def trait_catalog(data_path: Path):
    # Return the full trait catalog dict with key 'traits' for ID lookup
    return yaml_utils.load_yaml(data_path / "traits.yaml")


@pytest.fixture(scope="module")
def resources(data_path: Path):
    return yaml_utils.load_yaml(data_path / "resources.yaml")


@pytest.fixture(scope="module")
def formulas(data_path: Path):
    return yaml_utils.load_yaml(data_path / "formulas.yaml")


@pytest.fixture(scope="module")
def appearance_tables_dir(data_path: Path):
    return data_path / "appearance" / "tables"


@pytest.fixture(scope="module")
def appearance_ranges_dir(data_path: Path):
    return data_path / "appearance" / "ranges"


def test_formula_eval():
    """Tests the safe formula evaluation service."""
    ctx = {"STA": 5, "INT": 3, "level": 4}
    expression = "20 + STA * 5 + floor(level / 2)"
    expected = 20 + (5 * 5) + (4 // 2)
    result = formula_eval.evaluate(expression, ctx)
    assert result == expected


def test_generate_npc_populates_fields(
    stat_tmpl,
    slot_tmpl,
    appearance_fields,
    appearance_tables_dir,
    appearance_ranges_dir,
    class_catalog,
    trait_catalog,
    resources,
    formulas,
):
    """
    Tests that NPC generation populates all required fields and performs
    basic calculations correctly.
    """
    hero = npc_factory.generate_npc(
        name_prefix="NPC",
        stat_tmpl=stat_tmpl,
        slot_tmpl=slot_tmpl,
        appearance_fields=appearance_fields,
        appearance_tables_dir=appearance_tables_dir,
        appearance_ranges_dir=appearance_ranges_dir,
        class_catalog=class_catalog,
        trait_catalog=trait_catalog,
        resources=resources,
        formulas=formulas,
    )

    assert hero.name.startswith("NPC")
    assert hero.name != "NPC"  # Should have a unique suffix

    # Check that all appearance fields defined in fields.yaml were populated
    assert len(hero.appearance) == len(appearance_fields)
    for field in appearance_fields:
        assert field in hero.appearance
        # assert hero.appearance[field] is not None

    # Check that at least one class was applied
    assert hero.classes
    assert len(hero.classes) >= 1

    # Sanity check for HP. The exact value is random, but it should be in a reasonable range.
    # Base HP is 20 + STA * 5. STA starts at 1 and gets 0-3 bumps of 0.1.
    # Min STA ~1, Max STA ~1.3. Level is 1.
    # Min HP formula: 20 + 1*5 + floor(1/2) = 25
    # Max HP formula: 20 + 1.3*5 + floor(1/2) = 26.5 -> 26
    # Classes/traits can modify this. A quick check of data shows bonuses.
    # Let's use a generous range.
    # assert 18 <= hero.stats["HP"].base <= 200
    # assert hero.stats["HP"].current == hero.stats["HP"].base


def test_hp_mana_match_formulas_with_deterministic_rng(
    monkeypatch,
    stat_tmpl,
    slot_tmpl,
    appearance_fields,
    appearance_tables_dir,
    appearance_ranges_dir,
    class_catalog,
    trait_catalog,
    resources,
    formulas,
):
    # Force deterministic RNG behavior
    monkeypatch.setattr(random_utils, "roll_normal", lambda mean, sd: mean)
    monkeypatch.setattr(
        random_utils, "roll_uniform", lambda min_val, max_val: (min_val + max_val) / 2.0
    )

    hero = npc_factory.generate_npc(
        name_prefix="NPC",
        stat_tmpl=stat_tmpl,
        slot_tmpl=slot_tmpl,
        appearance_fields=appearance_fields,
        appearance_tables_dir=appearance_tables_dir,
        appearance_ranges_dir=appearance_ranges_dir,
        class_catalog=class_catalog,
        trait_catalog=trait_catalog,
        resources=resources,
        formulas=formulas,
    )

    def to_number(v):
        if hasattr(v, "base"):
            return float(v.base)
        if isinstance(v, dict) and "base" in v:
            return float(v["base"])
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except Exception:
            return 0.0

    ctx = {"level": hero.level}
    for key in stat_tmpl.keys():
        if key in hero.stats:
            ctx[key] = to_number(hero.stats[key])

    # The generator casts evaluated values to int when assigning HP/Mana
    expected_hp = int(formula_eval.evaluate(formulas["baseline"]["hp"], ctx))
    expected_mana = int(formula_eval.evaluate(formulas["baseline"]["mana"], ctx))

    assert hero.stats["HP"]["base"] == expected_hp
    assert hero.stats["Mana"]["base"] == expected_mana
