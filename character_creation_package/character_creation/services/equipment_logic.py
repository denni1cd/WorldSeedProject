from typing import Dict, Any


def item_fits_slot(item: Dict[str, Any], slot_id: str, slot_template: Dict[str, Any]) -> bool:
    """
    Return True if the item's 'slot' allows equipping into the given slot_id.

    The item's 'slot' can be:
    - a specific slot_id (string)
    - a slot category (string) that must match slot_template[slot_id]["cat"]
    - a list of either of the above; any match is OK
    """
    # Build a map of slot_id -> slot_definition regardless of nesting under 'slots'
    slot_map: Dict[str, Any] = (
        slot_template["slots"] if isinstance(slot_template.get("slots"), dict) else slot_template
    )

    allowed = item.get("slot")
    if allowed is None:
        return False

    allowed_list = allowed if isinstance(allowed, list) else [allowed]

    for allowed_entry in allowed_list:
        # Direct slot id match
        if allowed_entry == slot_id:
            return True
        # Category match using slot definition if available
        if slot_id in slot_map and allowed_entry == slot_map[slot_id].get("cat"):
            return True

    return False


def can_equip(
    character,
    item_id: str,
    slot_id: str,
    items_catalog: Dict[str, Any],
    slot_template: Dict[str, Any],
) -> bool:
    """Return False if slot invalid, item missing, or doesn't fit. Else True."""
    if "slots" in slot_template:
        slot_keys = slot_template["slots"].keys()
    else:
        slot_keys = slot_template.keys()
    if slot_id not in slot_keys:
        return False
    item = items_catalog.get(item_id)
    if not item:
        return False
    return item_fits_slot(item, slot_id, slot_template)
