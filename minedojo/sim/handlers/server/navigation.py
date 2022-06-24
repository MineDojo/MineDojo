# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
from minedojo.sim.handler import Handler


class NavigationDecorator(Handler):
    """
    Specifies the navigate goal.
    This class should enable the parameterization of all of the fields in the XML.

    When used to create a Gym environment, they should be passed to create_server_decorators.
    """

    def to_string(self) -> str:
        return "navigation_decorator"

    def xml_template(self) -> str:
        return str(
            """<NavigationDecorator>
                <randomPlacementProperties>
                    <maxRandomizedRadius>{{max_randomized_radius}}</maxRandomizedRadius>
                    <minRandomizedRadius>{{min_randomized_radius}}</minRandomizedRadius>
                    <maxRadius>{{max_radius}}</maxRadius>
                    <minRadius>{{min_radius}}</minRadius>
                    <block>{{block}}</block>
                    <placement>{{placement}}</placement>
                </randomPlacementProperties>
                <minRandomizedDistance>{{min_randomized_distance}}</minRandomizedDistance>
                <maxRandomizedDistance>{{max_randomized_distance}}</maxRandomizedDistance>
                <randomizeCompassLocation>{{randomize_compass_location | string | lower}}</randomizeCompassLocation>
            </NavigationDecorator>
            """
        )

    def __init__(
        self,
        max_randomized_radius: int = 64,
        min_randomized_radius: int = 64,
        min_randomized_distance: int = 0,
        max_randomized_distance: int = 8,
        max_radius: int = 8,
        min_radius: int = 0,
        block: str = "diamond_block",
        placement: str = "fixed_surface",
        randomize_compass_location: bool = False,
    ):
        """Initialize navigation decorator

        :param max_randomized_radius: Maximum value to randomize placement
        :param min_randomized_radius: Minimum value to randomize placement
        :param max_radius: Maximum radius to place in the X axis
        :param min_radius: Minimum radius to place in the X axis
        :param block: Type of block to appear.
        :param placement: 'fixed_surface' or otherwise (see XML schema)
        """
        self.max_randomized_radius = max_randomized_radius
        self.min_randomized_radius = min_randomized_radius
        self.max_radius = max_radius
        self.min_radius = min_radius
        self.block = block
        self.placement = placement
        self.randomize_compass_location = randomize_compass_location
        self.min_randomized_distance = min_randomized_distance
        self.max_randomized_distance = max_randomized_distance
