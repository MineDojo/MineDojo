# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
from minedojo.sim.handlers.agent.actions.craft import CraftAction


class SmeltAction(CraftAction):
    """
    An action handler for crafting items when agent is in view of a crafting table

    Note when used along side Craft Item, block lists must be disjoint or from_universal will fire multiple times
    """

    _command = "smeltNearby"

    def to_string(self):
        return "smelt"

    def xml_template(self) -> str:
        return str("<NearbySmeltCommands/>")

    def from_universal(self, obs):
        if (
            "diff" in obs
            and "smelted" in obs["diff"]
            and len(obs["diff"]["smelted"]) > 0
        ):
            try:
                x = self._univ_items.index(obs["diff"]["smelted"][0]["item"])
                return obs["diff"]["smelted"][0]["item"].split("minecraft:")[-1]
            except ValueError:
                return self._default
                # return self._items.index('other')
        else:
            return self._default
