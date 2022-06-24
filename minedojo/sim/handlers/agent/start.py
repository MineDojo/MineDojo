# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""
Agent start handlers define agent start conditions such as inventory items and health.

When used to create a Gym environment, they should be passed to :code:`create_agent_start`
"""
import random
from typing import Dict, List, Union

from minedojo.sim.handler import Handler


class InventoryAgentStart(Handler):
    """
    Sets the start inventory of the agent by slot id.

    Example usage:

    .. code-block:: python

        InventoryAgentStart({
            0: {'type':'dirt', 'quantity':10},
            # metadata specifies the type of planks (e.g. oak, spruce)
            1: {'type':'planks', 'metadata': 1, 'quantity':5},
            5: {'type':'log', 'quantity':1},
            6: {'type':'log', 'quantity':2},
            32: {'type':'iron_ore', 'quantity':4
        })
    """

    def to_string(self) -> str:
        return "inventory_agent_start"

    def xml_template(self) -> str:
        return str(
            """<Inventory>
            {% for  slot in inventory %}
                <InventoryObject
                    slot="{{ slot }}"
                    type="{{ inventory[slot]['type'] }}"
                    metadata="{{ inventory[slot].get('metadata', 0) }}"
                    quantity="{{ inventory[slot]['quantity'] }}"
                    />
            {% endfor %}
            </Inventory>
            """
        )

    def __init__(self, inventory: Dict[int, Dict[str, Union[str, int]]]):
        """
        Args:
            inventory (Dict[int, Dict[str, Union[str,int]]]): The inventory slot description.
        """
        self.inventory = inventory


class SimpleInventoryAgentStart(InventoryAgentStart):
    """
    Sets the start inventory of the agent sequentially.

    Example usage:

    .. code-block:: python

        SimpleInventoryAgentStart([
            {'type':'dirt', 'quantity':10},
            {'type':'planks', 'quantity':5},
            {'type':'log', 'quantity':1},
            {'type':'iron_ore', 'quantity':4}
        ])
    """

    def __init__(self, inventory: List[Dict[str, Union[str, int]]]):
        """Creates a simple inventory agent start."""
        super().__init__({i: item for i, item in enumerate(inventory)})


class RandomInventoryAgentStart(InventoryAgentStart):
    """
    Sets the agent start inventory by randomly distributing items throughout its inventory slots.
    Note: This has no effect on inventory observation handlers.

    Example usage:

    .. code-block:: python

        RandomInventoryAgentStart(
            {'dirt': 10, 'planks': 5}
        )
    """

    def __init__(self, inventory: Dict[str, Union[str, int]], use_hotbar: bool = False):
        """Creates an inventory where items are placed in random positions"""
        self.inventory = inventory
        self.slot_range = (0, 36) if use_hotbar else (10, 36)

    def xml_template(self) -> str:
        lines = ["<Inventory>"]
        for item, quantity in self.inventory.items():
            slot = random.randint(*self.slot_range)
            lines.append(
                f'<InventoryObject slot="{slot}" type="{item}" quantity="{quantity}"/>'
            )
        lines.append("</Inventory>")
        return "\n".join(lines)


class AgentStartBreakSpeedMultiplier(Handler):
    """
    Sets the break speed multiplier (how fast the agent can break blocks)

    See here for more information: https://minecraft.fandom.com/el/wiki/Breaking

    Example usage:

    .. code-block:: python

        AgentStartBreakSpeedMultiplier(2.0)
    """

    def to_string(self) -> str:
        return f"agent_start_break_speed_multiplier({self.multiplier})"

    def xml_template(self) -> str:
        return str("""<BreakSpeedMultiplier>{{multiplier}}</BreakSpeedMultiplier>""")

    def __init__(self, multiplier=1.0):
        self.multiplier = multiplier


class AgentStartPlacement(Handler):
    """
    Sets for the agent start location

    Example usage:

    .. code-block:: python

        AgentStartPlacement(x=5, y=70, z=4, yaw=0, pitch=0)
    """

    def to_string(self) -> str:
        return f"agent_start_placement({self.x}, {self.y}, {self.z}, {self.yaw}, {self.pitch})"

    def xml_template(self) -> str:
        return str(
            """<Placement x="{{x}}" y="{{y}}" z="{{z}}" yaw="{{yaw}}" pitch="{{pitch}}"/>"""
        )

    def __init__(self, x, y, z, yaw, pitch=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch


class AgentStartNear(Handler):
    """
    Starts agent near another agent

    Example usage:

    .. code-block:: python

        AgentStartNear("MineRLAgent0", min_distance=2, max_distance=10, max_vert_distance=3)
    """

    def to_string(self) -> str:
        return f"agent_start_near({self.anchor_name}, h {self.min_distance} - {self.max_distance}, v {self.max_vert_distance})"

    def xml_template(self) -> str:
        return str(
            """<NearPlayer>
                    <Name>{{anchor_name}}</Name>
                    <MaxDistance>{{max_distance}}</MaxDistance>
                    <MinDistance>{{min_distance}}</MinDistance>
                    <MaxVertDistance>{{max_vert_distance}}</MaxVertDistance>
                    <LookingAt>true</LookingAt>
               </NearPlayer>"""
        )

    def __init__(
        self,
        anchor_name="MineRLAgent0",
        min_distance=2,
        max_distance=10,
        max_vert_distance=3,
    ):
        self.anchor_name = anchor_name
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.max_vert_distance = max_vert_distance


class StartingHealthAgentStart(Handler):
    """
    Sets the starting health of the agent

    Example usage:

    .. code-block:: python

        StartingHealthAgentStart(max_health=20, health=2.5)

    :code:`max_health` sets the maximum amount of health the agent can have
    :code:`health` sets amount of health the agent starts with (max_health if not specified)
    """

    def to_string(self) -> str:
        return "starting_health_agent_start"

    def xml_template(self) -> str:
        if self.health is None:
            return str("""<StartingHealth maxHealth="{{ max_health }}"/>""")
        else:
            return str(
                """<StartingHealth maxHealth="{{ max_health }}" health="{{ health }}"/>"""
            )

    def __init__(self, max_health: float = 20, health: float = None):
        """ """
        self.health = health
        self.max_health = max_health


class StartingFoodAgentStart(Handler):
    """
    Sets the starting food and/or food saturation of the agent.

    Example usage:

    .. code-block:: python

        StartingFoodAgentStart(food=2.5, food_saturation=1)

    Args:
        :code:`food`: The amount of food the agent starts out with
        :code:`food_saturation`: Determines how fast the hunger level depletes, defaults to 5
    """

    def to_string(self) -> str:
        return "starting_food_agent_start"

    def xml_template(self) -> str:
        return str("""<StartingFood food="{{ food }}"/>""")

    def __init__(self, food: int = 20):
        self.food = food


class RandomizedStartDecorator(Handler):
    def to_string(self) -> str:
        return "randomized_start_decorator"

    def xml_template(self) -> str:
        return str("""<RandomizedStartDecorator/>""")


class LowLevelInputsAgentStart(Handler):
    def to_string(self) -> str:
        return "low_level_inputs"

    def xml_template(self) -> str:
        return "<LowLevelInputs>true</LowLevelInputs>"
