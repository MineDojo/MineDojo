# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import typing
from typing import Any, Sequence
from collections.abc import Iterable

import numpy as np

from minedojo.sim import spaces
from minedojo.sim.handlers import util
from minedojo.sim.handlers.translation import TranslationHandler


class Action(TranslationHandler):
    """
    An action handler based on commands
    # Todo: support blacklisting commands. (note this has to work with merging somehow)
    """

    def __init__(self, command: str, space: spaces.MineRLSpace):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """
        self._command = command
        super().__init__(space)

    @property
    def command(self):
        return self._command

    def to_string(self):
        return self._command

    def to_hero(self, x):
        """
        Returns a command string for the multi command action.
        :param x:
        :return:
        """
        cmd = ""
        verb = self.command

        if isinstance(x, np.ndarray):
            flat = x.flatten().tolist()
            flat = [str(y) for y in flat]
            adjective = " ".join(flat)
        elif isinstance(x, Iterable) and not isinstance(x, str):
            adjective = " ".join([str(y) for y in x])
        else:
            adjective = str(x)
        cmd += "{} {}".format(verb, adjective)

        return cmd

    def __or__(self, other):
        if not self.command == other.command:
            raise ValueError(
                f"Command must be the same between {self.command} and {other.command}"
            )
        return self


class BaseItemListAction(Action):
    def __init__(
        self,
        command: str,
        items: Sequence[str],
        _default="none",
        _other="other",
    ):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.

        Args:
            command: The 'verb' argument processed by Malmo handlers. This is also
                the default key used by this action in the MineRL env's Dict
                action space.
            items: A list of string item IDs. For convenience, dictionaries in the
                style of those used by `handlers.InventoryAgentStart` can also
                be passed in. In the case of dictionaries, the "type" key is
                unpacked to get the item ID.
        """
        self._items = list(items)
        self._univ_items = ["minecraft:" + item for item in items]
        if _other not in self._items:
            self._items.append(_other)
        if _default not in self._items:
            self._items.append(_default)
        self._default = _default
        self._other = _other
        super().__init__(
            command,
            spaces.Enum(*self._items, default=self._default),
        )

    def __or__(self, other):
        """
        Merges two ItemListCommandActions into one by unioning their items.
        Assert that the commands are the same.
        """

        if not isinstance(other, self.__class__):
            raise TypeError("other must be an instance of ItemListCommandAction")

        if self._command != other._command:
            raise ValueError("Command must be the same for merging")

        new_items = list(set(self._items) | set(other._items))
        return self.__class__(
            command=self._command,
            items=new_items,
            _default=self._default,
            _other=self._other,
        )

    def __eq__(self, other):
        """
        Asserts equality between item list command actions.
        """
        if not isinstance(other, type(self)):
            return False
        if self._command != other._command:
            return False
        if sorted(self._items) != sorted(other._items):
            return False

        return True

    def from_hero(self, x: typing.Dict[str, Any]):
        pass

    def xml_template(self) -> str:
        pass

    @property
    def items(self):
        return self._items

    @property
    def universal_items(self):
        return self._univ_items

    @property
    def default(self):
        return self._default

    def from_universal(self, x):
        raise NotImplementedError


class ItemListAction(BaseItemListAction):
    """
    An action handler based on a list of item IDs without metadata constraints.
    The action space is determined by the length of the list plus one

    Eventually, we should transitions all subclasses of this class to use
    `ItemWithMetadataListAction` instead so that all action item spaces can include
    metadata-constrained item IDs.
    """

    def __init__(self, command: str, items: list, **kwargs):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all spaces for each individual command.
        """
        assert all(["#" not in item for item in items])
        super().__init__(command, items, **kwargs)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}" f"(command={self.command}, items={self.items})"
        )


class ItemWithMetadataListAction(BaseItemListAction):
    """
    An action handler based on a list of item IDs with metadata constraints.
    The action space is determined by the length of the list plus one
    """

    def __init__(self, command, items, **kwargs):
        super().__init__(command, items, **kwargs)
        util.error_on_malformed_item_list(items, [self._other, self._default, "air"])

    def _preprocess_item_id(self, item_id: str) -> str:
        """
        Validate item type and metadata (i.e. errors if item_id is malformed), and
        returns an item_id in canonical form. The return value should be the same as the
        argument unless the item has no metadata constraint, in which case "#?" will be
        appended to the argument.
        """
        # Also validates item_id.
        item_type, metadata = util.decode_item_maybe_with_metadata(item_id)

        if not util.item_list_contains(self.items, item_type, metadata):
            raise ValueError(f"{item_id} is not found in {self.items}")
        return util.encode_item_with_metadata(item_type, metadata)

    def to_hero(self, x):
        canonical_item_id = self._preprocess_item_id(x)
        return super().to_hero(canonical_item_id)
