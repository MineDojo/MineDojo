"""
These handlers cause the episode to terminate based on certain agent conditions.

When used to create a Gym environment, they should be passed to :code:`create_agent_handlers`
"""
# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from typing import List, Dict, Union

from minedojo.sim.handler import Handler


#  <AgentQuitFromTouchingBlockType>
#     <Block type="diamond_block"/>
#     <Block type="iron_block"/>
# </AgentQuitFromTouchingBlockType>
class AgentQuitFromTouchingBlockType(Handler):
    """
    Terminates episode when agent touches one of the blocks in :code:`blocks`

    Example usage:

    .. code-block:: python

        AgentQuitFromTouchingBlockType([
            "gold_block", "oak_log"
        ])
    """

    def to_string(self) -> str:
        return "agent_quit_from_touching_block_type"

    def xml_template(self) -> str:
        return str(
            """<AgentQuitFromTouchingBlockType>
                    {% for block in blocks %}
                    <Block type="{{ block }}"/>
                    {% endfor %}
                </AgentQuitFromTouchingBlockType>"""
        )

    def __init__(self, blocks: List[str]):
        """Creates a reward which will cause the player to quit when they touch a block."""
        self.blocks = blocks


#  <AgentQuitFromDeath/>
class AgentQuitFromDeath(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_death"

    def xml_template(self) -> str:
        return str("""<AgentQuitFromDeath/>""")


# <AgentQuitFromCraftingItem>
#     <Item type="iron_pickaxe"/>
#     <Item type="wooden_axe"/>
#     <Item type="chest"/>
# </AgentQuitFromCraftingItem>
class AgentQuitFromCraftingItem(Handler):
    """
    Terminates episode when agent crafts one of the items in :code:`items`

    Example usage:

    .. code-block:: python

        AgentQuitFromCraftingItem([
            dict(type="iron_axe", amount=1), dict(type="diamond_block", amount=5)
        ])
    """

    def to_string(self) -> str:
        return "agent_quit_from_crafting_item"

    def xml_template(self) -> str:
        return str(
            """<AgentQuitFromCraftingItem>
                    {% for item in items %}
                    <Item type="{{ item.type}}" amount="{{ item.amount }}"/>
                    {% endfor %}
                </AgentQuitFromCraftingItem>"""
        )

    def __init__(self, items: List[Dict[str, Union[str, int]]]):
        """Creates a reward which will cause the player to quit when they have finished crafting something."""
        self.items = items

        for item in self.items:
            assert "type" in item, "{} does contain `type`".format(item)
            assert "amount" in item, "{} does not contain `amount`".format(item)


#  <AgentQuitFromPossessingItem>
#     <Item type="log" amount="64"/>
# </AgentQuitFromPossessingItem>
class AgentQuitFromPossessingItem(Handler):
    """
    Terminates episode when agent obtains one of the items in :code:`items`

    Example usage:

    .. code-block:: python

        AgentQuitFromPossessingItem([
            dict(type="golden_apple", amount=3), dict(type="diamond", amount=1)
        ])
    """

    def to_string(self) -> str:
        return "agent_quit_from_possessing_item"

    def xml_template(self) -> str:
        return str(
            """<AgentQuitFromPossessingItem>
                   {% for item in items %}
                   <Item type="{{ item.type }}" amount="{{ item.amount }}"/>
                   {% endfor %}
               </AgentQuitFromPossessingItem>"""
        )

    def __init__(self, items: List[Dict[str, Union[str, int]]]):
        assert isinstance(items, list)
        self.items = items
        # Assert that all the items have the correct fields for the XML.
        for item in self.items:
            assert "type" in item, "{} does contain `type`".format(item)
            assert "amount" in item, "{} does not contain `amount`".format(item)
