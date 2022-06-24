# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import minedojo.sim.spaces as spaces
from minedojo.sim.handlers.agent.action import Action


class KeybasedCommandAction(Action):
    """
    A command action which is generated from human keypresses in anvil.
    Examples of such actions are movement actions, etc.

    This is not to be confused with keyboard acitons, wehreby both anvil and malmo
    simulate and act on direct key codes.

    Combinations of KeybasedCommandActions yield actions like:

    .. code-block:: json

        {
            “move” : 1,
            “jump”: 1
        }
    where move and jump are the commands, which correspond to keys like 'W', 'SPACE', etc.

    This is as opposed to keyboard actions (see the following class definition in keyboard.py)
    which yield actions like:

    .. code-block:: json

        {
            "keyboard" : {
                "W" : 1,
                "A": 1,
                "S": 0,
                "E": 1,
                ...
            }
        }
    More information can be found in the unification document (internal).
    """

    def to_string(self):
        return self.command

    def xml_template(self) -> str:
        """Notice how all of the instances of keybased command actions,
        of which there will be typically many in an environment spec,
        correspond to exactly the same XML stub.

        This is discussed at length in the unification proposal
        and is a chief example of where manifest consolidation is needed.
        """
        return str("<HumanLevelCommands/>")

    def __init__(self, command, *keys):
        if len(keys) == 2:
            # Like move or strafe. Example: -1 for left, 1 for right
            super().__init__(command, spaces.DiscreteRange(-1, 2))
        else:
            # Its a n-key action with discrete items.
            # Eg hotbar actions
            super().__init__(command, spaces.Discrete(len(keys) + 1))
        self.keys = keys

    def from_universal(self, x):
        # actions_mapped is just the raw key codes.
        actions_mapped = list(x["custom_action"]["actions"].keys())
        offset = self.space.begin if isinstance(self.space, spaces.DiscreteRange) else 0
        default = 0

        for i, key in enumerate(self.keys):
            if key in actions_mapped:
                if isinstance(self.space, spaces.DiscreteRange):
                    return i * 2 + offset
                else:
                    return i + 1 + offset

        return default


# TODO: This will be useful for when full keyboard actions are introduced.
# class KeyboardAction(TranslationHandler):
#     """Enables a set of keyboard actions.
#     This handler correspomds direcrtly with the HumanLevelCommands handler
#     in MissionHandlers.xsd.

#     """
#     def xml_template(self) -> str:
#         return str("""
#             <HumanLevelCommands>
#                 <ModifierList type="allow-list">
#                     {% for command in commands %}
#                         <command>{{ command }}</command>
#                     {% endfor %}
#                 </ModifierList>
#             </HumanLevelCommands>
#             """)


#     def to_string(self) -> str:
#         return "keyboard"

#     def __init__(self, keymap : typing.Dict[str, str]):
#         """Initializes the keyboard action object with a keymap
#         Anvil rendered keypress ID's and Malmo command actions corresponding to the human level commands object.

#         Args:
#             keymap (Dict[str, str]): A keymap between anvil keys & Malmo commands (see KEYMAP)
#         """
#         self.keymap = keymap

#         super().__init__(spaces.Dict(
#             {
#                 v: spaces.Discrete(1) for v in keymap.values()
#             }
#         ))

#     def xml(self) -> str:
#         return self.TEMPLATE.render(commands=self.keymap.values())

#     def to_hero(self, x : typing.Dict[str, np.ndarray]) -> str:
#         """ Joins all of the commands in X to a string by new lines.
#         First joins the keys and values in X with a space.

#         Args:
#             x (typing.Dict[str, Any]): A KeyboardAction.
#         """
#         return   '\n'.join(['%s %s' % (k, v) for k, v in x.items()])

#     def from_universal(self, x: typing.Dict[str, Any]) -> typing.Dict[str, np.ndarray]:
#         """Finds all of the keys in the universal json corresponding to keypresses
#         and if they are present produces an observation dictionary with keymap keys
#         having value 1 and otherwise 0.
#         """
#         actions_mapped = list(x['custom_action']['actions'].keys())
#         # actions_mapped is just the raw key codes.

#         out = self.space.no_op()
#         out.update({
#             out[self.keymap[a]] : np.array(1, dtype=np.int) for a in actions_mapped
#         })


#         return out

#     def __or__(self, other):
#         """Combines the keymaps from both dealios.
#         """
#         super().__or__(other)
#         new_keymap = {}
#         new_keymap.update(self.keymap)
#         new_keymap.update(other.keymap)
#         return  KeyboardAction(keymap=new_keymap)
