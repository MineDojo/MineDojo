# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import numpy as np

from minedojo.sim import spaces
from minedojo.sim.handlers.translation import (
    KeymapTranslationHandler,
    TranslationHandlerGroup,
)


__all__ = ["CompassObservation"]


class CompassObservation(TranslationHandlerGroup):
    """
    Defines compass observations.

    Args:
        angle (bool, optional): Whether or not to include angle observation. Defaults to True.
        distance (bool, optional): Whether or not ot include distance observation. Defaults to False.

    Example usage:

    .. code-block:: python

        # A compass observation object which gives angle and distance information
        CompassObservation(True, True)
    """

    def to_string(self) -> str:
        return "compass"

    def xml_template(self) -> str:
        return str("""<ObservationFromCompass/>""")

    def __init__(self, angle=True, distance=False):
        """Initializes a compass observation."""

        assert angle or distance, "Must observe either angle or distance"

        handlers = []

        if angle:
            handlers.append(_CompassAngleObservation())
        if distance:
            handlers.append(
                KeymapTranslationHandler(
                    hero_keys=["distanceToCompassTarget"],
                    univ_keys=["compass", "distance"],
                    to_string="distance",
                    space=spaces.Box(low=0, high=np.inf, shape=(), dtype=np.float32),
                )
            )

        super(CompassObservation, self).__init__(handlers=handlers)


class _CompassAngleObservation(KeymapTranslationHandler):
    """
    Handles compass angle observations (converting to the correct angle offset normalized.)
    """

    def __init__(self):
        super().__init__(
            hero_keys=["compassAngle"],
            univ_keys=["compass", "angle"],
            space=spaces.Box(low=-180.0, high=180.0, shape=(), dtype=np.float32),
            to_string="angle",
        )

    def from_universal(self, obs):
        y = np.array(((super().from_universal(obs) * 360.0 + 180) % 360.0) - 180)
        return y
