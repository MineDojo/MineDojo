# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import logging

from minedojo.sim.handlers.agent import action
from minedojo.sim.handlers import util
import minedojo.sim.mc_meta.mc as mc


class EquipAction(action.ItemWithMetadataListAction):
    """
    An action handler for observing a list of equipped items
    """

    logger = logging.getLogger(__name__ + ".EquipAction")

    def __init__(self, items: list, _default="none", _other="other"):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action
        """
        super().__init__("equip", items, _default=_default, _other=_other)
        self._previous_id = self._default
        self._previous_type = None
        self._previous_metadata = None

    def xml_template(self) -> str:
        return str("<EquipCommands/>")

    def reset(self):
        self._previous_id = self._default

    def from_universal(self, obs) -> str:
        slots_gui_type = obs["slots"]["gui"]["type"]
        if slots_gui_type == "class net.minecraft.inventory.ContainerPlayer":
            hotbar_index = int(obs["hotbar"])
            hotbar_slot = obs["slots"]["gui"]["slots"][-10 + hotbar_index]

            if len(hotbar_slot.keys()) == 0:
                # Really we should be returning air, and requiring that it exists in `self.items`?
                return self._default

            item_type = mc.strip_item_prefix(hotbar_slot["name"])
            metadata = hotbar_slot["variant"]
            assert metadata in range(16)
            id = util.get_unique_matching_item_list_id(
                self.items, item_type, metadata, clobber_logs=False
            )
            if id is None:
                # Matching item ID not found because item_type + metadata is outside of item list.
                # Return "other" if this combination
                # of item_type + metadata is different than the previous item step. (New other item
                # equipped.)
                # Otherwise, return "none" to indicate that the equipped item stack has not changed.
                if (
                    self._previous_type == item_type
                    and self._previous_metadata == metadata
                ):
                    result = self._default
                else:
                    result = self._other
            elif id == self._previous_id:
                result = self._default
            else:
                result = id

            self._previous_id = id
            self._previous_type = item_type
            self._previous_metadata = metadata
            return result
        else:
            expected_ignore_types = (  # Filter these out to reduce stderr clutter
                "class net.minecraft.inventory.ContainerWorkbench",
                "class net.minecraft.inventory.ContainerFurnace",
                "class net.minecraft.inventory.ContainerChest",
                "class net.minecraft.inventory.ContainerMerchant",
            )

            if slots_gui_type not in expected_ignore_types:
                self.logger.debug(
                    f"Unexpected slots_gui_type={slots_gui_type}, "
                    f"Abandoning processing and simply returning '{self._default}'"
                )
            return self._default
