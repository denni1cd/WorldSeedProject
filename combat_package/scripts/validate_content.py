from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from combat.loaders.pack_loader import merge_content_with_packs
from combat.validators.validate import validate_bundle


def main():
    data_root = Path(__file__).parents[1] / "combat" / "data"
    bundle, merge_errors = merge_content_with_packs(data_root)
    errs = list(merge_errors) + validate_bundle(bundle)
    if errs:
        print("VALIDATION: FAIL")
        for e in errs:
            print(" -", e)
        raise SystemExit(1)
    print("VALIDATION: PASS — all checks OK")


if __name__ == "__main__":
    main()
