from __future__ import annotations

from pathlib import Path

from character_creation.loaders.content_packs_loader import (
    load_packs_config,
    load_and_merge_enabled_packs,
)


def main() -> None:
    root = Path(__file__).parents[1] / "character_creation" / "data"
    cfg = load_packs_config(root / "content_packs.yaml")
    merged = load_and_merge_enabled_packs(root, cfg)

    enabled = cfg.get("enabled", [])
    policy = (cfg.get("merge") or {}).get("on_conflict", "skip")
    print(f"Enabled packs: {', '.join(enabled) if enabled else '(none)'}")
    print(f"Merge policy: {policy}")

    def count(key: str) -> int:
        v = merged.get(key)
        if key in {"classes", "races", "items"}:
            return len(v or [])
        if key == "traits":
            return len((v or {}).keys())
        return 0

    print("Counts after merging:")
    print(f"  classes: {count('classes')}")
    print(f"  traits:  {count('traits')}")
    print(f"  races:   {count('races')}")
    print(f"  items:   {count('items')}")

    tables = merged.get("appearance_tables") or {}
    if tables:
        print("Appearance tables extended:")
        for name, values in tables.items():
            print(f"  {name}: +{len(values)} values")


if __name__ == "__main__":
    main()
