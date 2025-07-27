import pytest
from character_creation.services.creation_logic import available_starting_classes, validate_traits
from character_creation.loaders import classes_loader, traits_loader, stats_loader
from pathlib import Path

# Paths relative to test file location
DATA_ROOT = Path(__file__).parents[2] / "character_creation_package" / "character_creation" / "data"


@pytest.fixture
def stat_tmpl():
    return stats_loader.load_stat_template(DATA_ROOT / "stats" / "stats.yaml")


@pytest.fixture
def class_catalog():
    return classes_loader.load_class_catalog(DATA_ROOT / "classes.yaml")


@pytest.fixture
def trait_catalog():
    return traits_loader.load_trait_catalog(DATA_ROOT / "traits.yaml")


def test_available_starting_classes(stat_tmpl, class_catalog):
    result = available_starting_classes(stat_tmpl, class_catalog)
    for cls in result:
        assert not cls.get(
            "prereq"
        ), f"Class {cls.get('id', cls.get('name'))} has prereq: {cls.get('prereq')}"


def test_validate_traits(trait_catalog):
    traits = trait_catalog.get("traits", {})
    valid_ids = list(traits.keys())[:2]
    unknown_ids = ["not_a_trait", "also_fake"]
    input_ids = valid_ids + unknown_ids + valid_ids  # include duplicates
    result = validate_traits(input_ids, trait_catalog)
    # Only valid, deduped ids
    assert set(result) == set(valid_ids)
    assert len(result) == len(set(valid_ids))
    for tid in result:
        assert tid in traits
