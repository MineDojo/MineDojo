# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import logging
from typing import Any, Dict, List

import numpy as np

from .. import spaces as spaces
from ..handler import Handler


class TranslationHandler(Handler):
    """
    An agent handler to be added to the mission XML.
    This is useful as it defines basically all of the interfaces
    between universal action format, hero (malmo), and herobriane (ML stuff).
    """

    def __init__(self, space: spaces.MineRLSpace, **other_kwargs):
        self.space = space

    def from_hero(self, x: Dict[str, Any]):
        """
        Converts a "hero" representation of an instance of this handler
        to a member of the space.
        """
        raise NotImplementedError()

    def to_hero(self, x) -> str:
        """
        Takes an instance of the handler, x in self.space, and maps it to
        the "hero" representation thereof.
        """
        raise NotImplementedError()

    def from_universal(self, x: Dict[str, Any]):
        """
        Converts a universal representation of the handler (e.g. universal action/observation)
        """
        raise NotImplementedError()


# TODO: ONLY WORKS FOR OBSERVATIONS.
# TODO: Consider moving this to observations.
class KeymapTranslationHandler(TranslationHandler):
    def __init__(
        self,
        hero_keys: List[str],
        univ_keys: List[str],
        space: spaces.MineRLSpace,
        default_if_missing=None,
        to_string: str = None,
        ignore_missing: bool = False,
    ):
        """
        Wrapper for simple observations which just remaps keys.
        :param keys: list of nested dictionary keys from the root of the observation dict
        :param space: gym space corresponding to the shape of the returned value
        :param default_if_missing: value for handler to take if missing in the observation dict
        :param ignore_missing: If we should throw a warning when corresponding json field is
            missing from the observation.
        """
        super().__init__(space)
        self._to_string = to_string if to_string else hero_keys[-1]
        self.hero_keys = hero_keys
        self.univ_keys = univ_keys
        self.default_if_missing = default_if_missing
        self.ignore_missing = ignore_missing

    @property
    def logger(self):
        return logging.getLogger(f"{__name__}.{self.to_string()}")

    def walk_dict(self, d, keys, dtype=None):
        for key in keys:
            if key in d:
                d = d[key]
            else:
                if self.default_if_missing is not None:
                    if not self.ignore_missing:
                        self.logger.error(
                            f"No {keys[-1]} observation! Yielding default value "
                            f"{self.default_if_missing} for {'/'.join(keys)}"
                        )
                    return np.array(self.default_if_missing, dtype=dtype)
                else:
                    raise KeyError()
        return np.array(d, dtype=dtype)

    def to_hero(self, x) -> str:
        """What does it mean to do a keymap translation here?
        Since hero sends things as commands perhaps we could generalize
        this beyond observations.
        """
        raise NotImplementedError()

    def from_hero(self, hero_dict, dtype=None):
        return self.walk_dict(hero_dict, self.hero_keys, dtype=dtype)

    def from_universal(self, univ_dict):
        return self.walk_dict(univ_dict, self.univ_keys)

    def to_string(self) -> str:
        return self._to_string


class TranslationHandlerGroup(TranslationHandler):
    """Combines several space handlers into a single handler group."""

    def __init__(self, handlers: List[TranslationHandler]):
        self.handlers = sorted(handlers, key=lambda x: x.to_string())
        super(TranslationHandlerGroup, self).__init__(
            spaces.Dict([(h.to_string(), h.space) for h in self.handlers])
        )

    def to_hero(self, x: Dict[str, Any]) -> str:
        """Produces a string from an object X contained in self.space
        into a string by calling all of the corresponding
        to_hero methods and joining them with new lines
        """

        return "\n".join(
            [self.handler_dict[s].to_hero(x[s]) for s in self.handler_dict]
        )

    def from_hero(self, x: Dict[str, Any]) -> Dict[str, Any]:
        """Applies the constituent from_hero methods on the object X
        and builds a dictionary with keys corresponding to the constituent
        handlers applied."""

        return {h.to_string(): h.from_hero(x) for h in self.handlers}

    def from_universal(self, x: Dict[str, Any]) -> Dict[str, Any]:
        """Performs the same operation as from_hero except with from_universal."""
        return {h.to_string(): h.from_universal(x) for h in self.handlers}

    @property
    def handler_dict(self) -> Dict[str, Handler]:
        return {h.to_string(): h for h in self.handlers}
