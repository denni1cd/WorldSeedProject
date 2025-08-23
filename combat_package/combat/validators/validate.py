from __future__ import annotations
from typing import Dict, Any, List
from .schema import (
    validate_damage_types,
    validate_abilities,
    validate_status_effects,
    validate_body_parts,
    validate_narration,
    cross_validate,
)


def validate_bundle(bundle: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    errs += validate_damage_types({"damage_types": bundle.get("damage_types", [])})
    errs += validate_abilities({"abilities": bundle.get("abilities", [])})
    errs += validate_status_effects(bundle.get("status_effects", {}))
    errs += validate_body_parts(bundle.get("body_parts", {}))
    errs += validate_narration(bundle.get("narration", {}))
    errs += cross_validate(bundle)
    return errs
