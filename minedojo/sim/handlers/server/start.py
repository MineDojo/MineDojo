# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
"""
Server start handlers allow you to set the initial state of the World (e.g. weather, time) 

When used to create a Gym environment, they should be passed to :code:`create_server_initial_conditions`
"""

#  <BiomeGenerator forceReset="true" biome="3"/>
from minedojo.sim.handler import Handler


# <Time>
#     <StartTime>6000</StartTime>
#     <AllowPassageOfTime>false</AllowPassageOfTime>
# </Time>
class TimeInitialCondition(Handler):
    """
    Sets the initial world time as well as whether time can pass.

    Example usage:

    .. code-block:: python

        # Sets time to morning and stops passing of time
        TimeInitialCondition(False, 23000)
    """

    def to_string(self) -> str:
        return "time_initial_condition"

    def xml_template(self) -> str:
        return str(
            """<Time>
                   {% if start_time is not none %}
                   <StartTime>{{start_time | string}}</StartTime>
                   {% endif %}
                   <AllowPassageOfTime>{{allow_passage_of_time | string | lower}}</AllowPassageOfTime>
                </Time>"""
        )

    def __init__(self, allow_passage_of_time: bool, start_time: int = None):
        self.start_time = start_time
        self.allow_passage_of_time = allow_passage_of_time


# <Weather>clear</Weather>
class WeatherInitialCondition(Handler):
    """
    Sets the initial weather condition in the world.

    Example usage:

    .. code-block:: python

        # Sets weather to thunder
        WeatherInitialCondition("thunder")

    """

    def to_string(self) -> str:
        return "weather_initial_condition"

    def xml_template(self) -> str:
        return str("""<Weather>{{weather | string }}</Weather>""")

    def __init__(self, weather: str):
        self.weather = weather


# <AllowSpawning>false</AllowSpawning>
class SpawningInitialCondition(Handler):
    """
    Note: This controls the spawning of MOBs instead of players!
    """

    def to_string(self) -> str:
        return "spawning_initial_condition"

    def xml_template(self) -> str:
        return str(
            """<AllowSpawning>{{allow_spawning | string | lower}}</AllowSpawning>"""
        )

    def __init__(self, allow_spawning: bool):
        self.allow_spawning = allow_spawning
