"""
If there is a crafting table or furnace nearby
"""
from typing import Any

import numpy as np

from minedojo.sim import spaces
from minedojo.sim.handlers.translation import TranslationHandler


class NearbyToolsObservation(TranslationHandler):
    def to_string(self) -> str:
        return "nearby_tools"

    def xml_template(self) -> str:
        return ""

    def __init__(self):
        space = spaces.Dict(
            {
                "table": spaces.Box(low=0, high=1, dtype=bool, shape=()),
                "furnace": spaces.Box(low=0, high=1, dtype=bool, shape=()),
            }
        )
        super().__init__(space=space)

    def from_hero(self, x: dict[str, Any]):
        return {
            "table": np.array(x["nearby_crafting_table"], dtype=bool),
            "furnace": np.array(x["nearby_furnace"], dtype=bool),
        }
