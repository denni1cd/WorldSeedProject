from typing import Dict, Any


def item_fits_slot(item: Dict[str, Any], slot_id: str, slot_template: Dict[str, Any]) -> bool:
    """Return True if slot_id is allowed by item's 'slot' field (str or list)."""
    slots = item.get("slot")
    # Accept slot_id if slot_template is nested under 'slots'
    if "slots" in slot_template:
        slot_keys = slot_template["slots"].keys()
    else:
        slot_keys = slot_template.keys()
    if isinstance(slots, str):
        return slots == slot_id and slot_id in slot_keys
    elif isinstance(slots, list):
        return slot_id in slots and slot_id in slot_keys
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
