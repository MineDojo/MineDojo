# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
from typing import Optional

from minedojo.sim.handlers.agent.action import ItemListAction


class PlaceBlock(ItemListAction):
    """
    An action handler for placing a specific block
    """

    def to_string(self):
        return "place"

    def xml_template(self) -> str:
        return str("<PlaceCommands/>")

    def __init__(self, blocks: list, _other=Optional[str], _default=Optional[str]):
        """
        Initializes the space of the handler to be one for each item in the list
        Requires 0th item to be 'none' and last item to be 'other' corresponding to
        no-op and non-listed item respectively
        """
        self._items = blocks
        self._command = "place"
        kwargs = {}
        if _other is not None:
            kwargs["_other"] = _other
        if _default is not None:
            kwargs["_default"] = _default
        super().__init__(self._command, self._items, **kwargs)
        self._prev_inv = None

    def from_universal(self, obs):
        try:
            for action in obs["custom_action"]["actions"].keys():
                try:
                    if int(action) == -99 and self._prev_inv is not None:

                        item_name = self._prev_inv[int(-10 + obs["hotbar"])][
                            "name"
                        ].split("minecraft:")[-1]
                        if item_name not in self._items:
                            raise ValueError()
                        else:
                            return item_name
                except ValueError:
                    return self._other
        except TypeError:
            print("Saw a type error in PlaceBlock")
            raise TypeError
        except KeyError:
            return self._default
        finally:
            try:
                self._prev_inv = obs["slots"]["gui"]["slots"]
            except KeyError:
                self._prev_inv = None

        return self._default
