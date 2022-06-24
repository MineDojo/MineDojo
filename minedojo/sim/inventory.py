from typing import NamedTuple, Optional, Dict, Union, Tuple

from minedojo.sim.mc_meta.mc import ALL_ITEMS


EQUIP_SLOTS = {
    "mainhand": 0,
    "offhand": 40,
    "head": 39,
    "chest": 38,
    "legs": 37,
    "feet": 36,
}
MIN_SLOT_IDX = 0
MAX_SLOT_IDX = 40
SLOT_IDX2NAME = {v: k for k, v in EQUIP_SLOTS.items()}


class InventoryItem(NamedTuple):
    # slot of the item occupies,
    # can be str specifying "main_hand", "off_hand", "head", etc... or int specifying the slot index
    slot: Union[str, int]
    name: str
    variant: Optional[int] = None
    quantity: Optional[int] = None


def parse_inventory_item(item: InventoryItem) -> Tuple[int, Dict[str, Union[str, int]]]:
    slot, name, variant, quantity = item.slot, item.name, item.variant, item.quantity
    if isinstance(slot, str):
        assert slot in EQUIP_SLOTS, f"Unknown slot {slot}"
        slot = EQUIP_SLOTS[slot]
    assert MIN_SLOT_IDX <= slot <= MAX_SLOT_IDX, f"invalid slot index {slot}"
    assert name in ALL_ITEMS, f"Unknown item {name}"
    variant = variant or 0
    quantity = quantity or 1
    return slot, {
        "type": name,
        "metadata": variant,
        "quantity": quantity,
    }


def map_slot_number_to_cmd_slot(slot_number: int) -> str:
    assert MIN_SLOT_IDX <= slot_number <= MAX_SLOT_IDX, "exceed slot index range"
    if slot_number in {0, 40}:
        return f"slot.weapon.{SLOT_IDX2NAME[slot_number]}"
    elif 36 <= slot_number <= 39:
        return f"slot.armor.{SLOT_IDX2NAME[slot_number]}"
    elif 1 <= slot_number <= 8:
        return f"slot.hotbar.{slot_number}"
    else:
        return f"slot.inventory.{slot_number - 9}"
