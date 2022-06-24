# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import numpy as np

import minedojo.sim.spaces as spaces
from minedojo.sim.handlers.agent.action import Action


class CameraAction(Action):
    """
    Uses <delta_pitch, delta_yaw> vector in degrees to rotate the camera. pitch range [-180, 180], yaw range [-180, 180]
    """

    def to_string(self):
        return "camera"

    def xml_template(self) -> str:
        return str("<CameraCommands/>")

    def __init__(self):
        # TODO (minerl): Document and clean this wierd _ magic.
        self._command = "camera"
        super().__init__(
            self.command,
            spaces.Box(
                low=-180,
                high=180,
                shape=(2,),
                dtype=float,
            ),
        )
