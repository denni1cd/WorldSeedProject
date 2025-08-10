from pathlib import Path

from character_creation.services.live_reload import CatalogReloader


def main() -> None:
    dr = Path(__file__).parents[1] / "character_creation" / "data"
    rel = CatalogReloader(dr)
    print("Watching data/ for changes... Ctrl+C to stop.")

    def on_update(cats, version, changes):  # noqa: ANN001
        classes = len(cats["class_catalog"].get("classes", []))
        traits = len(cats["trait_catalog"].get("traits", {}))
        races = len(cats["race_catalog"].get("races", []))
        items = len(cats["items_catalog"].get("items", []))
        print(
            f"[v{version}] Reload OK — classes={classes}, traits={traits}, races={races}, items={items}. Changed: {len(changes)}"
        )

    try:
        rel.watch(on_update, debounce_ms=300)
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    main()
