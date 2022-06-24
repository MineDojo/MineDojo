from minedojo.sim.handlers.agent import Action
from minedojo.sim.spaces import DiscreteRange, Dict


class SwapSlotAction(Action):
    """
    An action handler for swapping items in two slots
    """

    xml_command = "swapInventoryItems"

    def __init__(self, min_slot_idx: int = 0, max_slot_idx: int = 40):
        space = Dict(
            {
                "source_slot": DiscreteRange(begin=min_slot_idx, end=max_slot_idx + 1),
                "target_slot": DiscreteRange(begin=min_slot_idx, end=max_slot_idx + 1),
            }
        )
        super().__init__(command="swap_slot", space=space)

    def xml_template(self) -> str:
        return str("<InventoryCommands/>")

    def to_hero(self, x):
        return f'{self.xml_command} {x["source_slot"]} {x["target_slot"]}'
