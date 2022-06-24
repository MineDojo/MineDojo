"""
A true flat inventory handler
"""
from typing import Dict, Any

import numpy as np

from minedojo.sim import spaces
from minedojo.sim.handlers.translation import TranslationHandler


class TrueFlatInventoryObservation(TranslationHandler):
    n_slots = 36
    # exclude equipment slots
    excluded_slots = [36, 37, 38, 39, 40]

    def to_string(self) -> str:
        return "inventory"

    def xml_template(self) -> str:
        return str("""<ObservationFromFullInventory flat="false"/>""")

    def __init__(self):
        shape = (self.n_slots,)
        space = spaces.Dict(
            {
                "name": spaces.Text(shape=shape),
                # max variant index is 120, i.e., item id 383:120 spawn egg for villager
                # see https://minecraft-ids.grahamedgecombe.com/
                "variant": spaces.MultiDiscrete([121 for _ in range(self.n_slots)]),
                # min stack size is 0 (no item), max stack size is 64
                "quantity": spaces.Box(
                    low=0, high=64, shape=(self.n_slots,), dtype=np.float32
                ),
                # though durability in MC seems to be integer, we still use box with float32 here
                "max_durability": spaces.Box(
                    low=-1, high=np.inf, shape=shape, dtype=np.float32
                ),
                "cur_durability": spaces.Box(
                    low=-1, high=np.inf, shape=shape, dtype=np.float32
                ),
            }
        )
        super().__init__(space=space)

    def from_hero(self, obs_dict: Dict[str, Any]):
        assert "inventory" in obs_dict, "Missing inventory key in malmo json"
        raw_inventory = [
            item for item in obs_dict["inventory"] if item["inventory"] == "inventory"
        ]
        assert len(raw_inventory) == self.n_slots + len(self.excluded_slots), "INTERNAL"
        return {
            key: np.array(
                [
                    self._name_preprocess(slot_dict[key])
                    if key == "name"
                    else slot_dict[key]
                    for i, slot_dict in enumerate(raw_inventory)
                    if i not in self.excluded_slots
                ],
                dtype=self.space[key].dtype,
            ).reshape(self.space[key].shape)
            for key in self.space
        }

    @staticmethod
    def _name_preprocess(raw_name: str):
        if "_" in raw_name:
            return raw_name.replace("_", " ")
        else:
            return raw_name


class EquipmentObservation(TrueFlatInventoryObservation):
    n_slots = 6
    excluded_slots = list(range(1, 36))

    def to_string(self) -> str:
        return "equipment"
