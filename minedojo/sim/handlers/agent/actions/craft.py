# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
from typing import Optional

from minedojo.sim.handlers.agent.action import ItemListAction


class CraftAction(ItemListAction):
    """
    An action handler for crafting items
    """

    _command = "craft"

    def to_string(self):
        return "craft"

    def xml_template(self) -> str:
        return str("<SimpleCraftCommands/>")

    def __init__(self, items: list, _other=Optional[str], _default=Optional[str]):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action (command 0)

        Items are minecraft resource ID's
        """
        kwargs = {}
        if _other is not None:
            kwargs["_other"] = _other
        if _default is not None:
            kwargs["_default"] = _default
        super().__init__(self._command, items, **kwargs)

    def from_universal(self, obs):
        if (
            "diff" in obs
            and "crafted" in obs["diff"]
            and len(obs["diff"]["crafted"]) > 0
        ):
            try:
                x = self._univ_items.index(obs["diff"]["crafted"][0]["item"])
                return obs["diff"]["crafted"][0]["item"].split("minecraft:")[-1]
            except ValueError:
                return self._default
                # return self._items.index('other')
        else:
            return self._default


class CraftWithTableAction(CraftAction):
    """
    An action handler for crafting items when agent is in view of a crafting table
    """

    _command = "craftNearby"

    def to_string(self):
        return "craft_with_table"

    def xml_template(self) -> str:
        return str("<NearbyCraftCommands/>")
