from __future__ import annotations
from pathlib import Path
from combat.loaders.pack_loader import merge_content_with_packs
from combat.validators.validate import validate_bundle
import yaml
import shutil


def _data_root():
    return Path(__file__).parents[1] / "combat" / "data"


def test_merge_skip_policy_default():
    data_root = _data_root()
    cfg_path = data_root / "content_packs.yaml"

    # Save original config
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as fh:
            orig_config = fh.read()
    else:
        orig_config = ""

    try:
        cfg = {"enabled": ["starter_plus"], "policy": "skip"}
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        bundle, errs = merge_content_with_packs(data_root)
        assert not errs
        # heavy_strike should exist
        ids = {a["id"] for a in bundle["abilities"]}
        assert "heavy_strike" in ids
    finally:
        # Restore original config
        cfg_path.write_text(orig_config, encoding="utf-8")


def test_merge_override_policy_allows_replacement(tmp_path):
    data_root = _data_root()
    cfg_path = data_root / "content_packs.yaml"

    # Save original config
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as fh:
            orig_config = fh.read()
    else:
        orig_config = ""

    try:
        # create a temp pack that overrides basic_attack name
        pack_dir = data_root / "packs" / "override_test"
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "abilities.yaml").write_text(
            yaml.safe_dump(
                {
                    "abilities": [
                        {
                            "id": "basic_attack",
                            "name": "Basic Attack (OVERRIDE)",
                            "kind": "attack",
                            "formula": "ATT + WPN - ARM*0.6",
                            "damage_type": "slashing",
                            "targeting": "single_enemy",
                            "crit": {"chance": "0.05", "multiplier": 1.5},
                            "resource_cost": {},
                            "cooldown": 0,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        # enable it with override policy
        cfg = {"enabled": ["starter_plus", "override_test"], "policy": "override"}
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        bundle, errs = merge_content_with_packs(data_root)
        assert not errs
        # verify name replaced
        ba = next(a for a in bundle["abilities"] if a["id"] == "basic_attack")
        assert "(OVERRIDE)" in ba["name"]
    finally:
        # cleanup
        shutil.rmtree(pack_dir, ignore_errors=True)
        # Restore original config
        cfg_path.write_text(orig_config, encoding="utf-8")


def test_merge_error_policy_reports_conflict(tmp_path):
    data_root = _data_root()
    cfg_path = data_root / "content_packs.yaml"

    # Save original config
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as fh:
            orig_config = fh.read()
    else:
        orig_config = ""

    try:
        # create conflicting pack
        pack_dir = data_root / "packs" / "conflict_test"
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "abilities.yaml").write_text(
            yaml.safe_dump(
                {
                    "abilities": [
                        {
                            "id": "basic_attack",
                            "name": "Conflict",
                            "kind": "attack",
                            "formula": "ATT",
                            "damage_type": "slashing",
                            "targeting": "single_enemy",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        # set policy error
        cfg = {"enabled": ["conflict_test"], "policy": "error"}
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        bundle, errs = merge_content_with_packs(data_root)
        assert any("Conflict in abilities" in e for e in errs)
    finally:
        # cleanup
        shutil.rmtree(pack_dir, ignore_errors=True)
        # Restore original config
        cfg_path.write_text(orig_config, encoding="utf-8")


def test_validation_catches_bad_refs(tmp_path):
    data_root = _data_root()
    cfg_path = data_root / "content_packs.yaml"

    # Save original config
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as fh:
            orig_config = fh.read()
    else:
        orig_config = ""

    try:
        # Add a pack with an ability referencing unknown damage_type and status
        bad_dir = data_root / "packs" / "bad_refs"
        bad_dir.mkdir(parents=True, exist_ok=True)
        (bad_dir / "abilities.yaml").write_text(
            yaml.safe_dump(
                {
                    "abilities": [
                        {
                            "id": "mystery",
                            "name": "Mystery",
                            "kind": "attack",
                            "formula": "ATT",
                            "damage_type": "shadow",
                            "targeting": "single_enemy",
                            "on_hit": {"apply_status": [{"id": "hexed"}]},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        cfg = {"enabled": ["starter_plus", "bad_refs"], "policy": "skip"}
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        bundle, errs = merge_content_with_packs(data_root)
        all_errs = errs + validate_bundle(bundle)
        assert any("unknown damage_type 'shadow'" in e for e in all_errs)
        assert any("unknown status 'hexed'" in e for e in all_errs)
    finally:
        # cleanup
        shutil.rmtree(bad_dir, ignore_errors=True)
        # Restore original config
        cfg_path.write_text(orig_config, encoding="utf-8")
