import math
from typing import Union, Sequence

import gym
import numpy as np

from ...sim import MineDojoSim
from ....sim import spaces as spaces
from ....sim.mc_meta import mc as MC
from ....sim.inventory import InventoryItem


class NNActionSpaceWrapper(gym.Wrapper):
    """
    Action wrapper to transform native action space to a new space friendly to train NNs
    """

    def __init__(
        self,
        env: Union[MineDojoSim, gym.Wrapper],
        discretized_camera_interval: Union[int, float] = 15,
        strict_check: bool = True,
    ):
        assert (
            "equip" in env.action_space.keys()
            and "place" in env.action_space.keys()
            and "swap_slot" not in env.action_space.keys()
        ), "please use this wrapper with event_level_control = True"
        assert (
            "inventory" in env.observation_space.keys()
        ), f"missing inventory from obs space"
        super().__init__(env=env)

        n_pitch_bins = math.ceil(360 / discretized_camera_interval) + 1
        n_yaw_bins = math.ceil(360 / discretized_camera_interval) + 1

        self.action_space = spaces.MultiDiscrete(
            [
                3,  # forward and back, 0: noop, 1: forward, 2: back
                3,  # 0: noop, 1: left, 2: right
                4,  # 0: noop, 1: jump, 2: sneak, 3: sprint
                n_pitch_bins,  # camera pitch, 0: -180, n_pitch_bins - 1: +180
                n_yaw_bins,  # camera yaw, 0: -180, n_yaw_bins - 1: +180,
                8,  # functional actions, 0: no_op, 1: use, 2: drop, 3: attack 4: craft 5: equip 6: place 7: destroy
                len(MC.ALL_CRAFT_SMELT_ITEMS),  # arg for "craft"
                MC.N_INV_SLOTS,  # arg for "equip", "place", and "destroy"
            ],
            noop_vec=[
                0,
                0,
                0,
                (n_pitch_bins - 1) // 2,
                (n_yaw_bins - 1) // 2,
                0,
                0,
                0,
            ],
        )
        self._cam_interval = discretized_camera_interval
        self._inventory_names = None
        self._strict_check = strict_check

    def action(self, action: Sequence[int]):
        """
        NN action to Malmo action
        """
        assert self.action_space.contains(action)
        destroy_item = (False, None)
        noop = self.env.action_space.no_op()

        # ------ parse main actions ------
        # parse forward and back
        if action[0] == 1:
            noop["forward"] = 1
        elif action[0] == 2:
            noop["back"] = 1
        # parse left and right
        if action[1] == 1:
            noop["left"] = 1
        elif action[1] == 2:
            noop["right"] = 1
        # parse jump sneak and sprint
        if action[2] == 1:
            noop["jump"] = 1
        elif action[2] == 2:
            noop["sneak"] = 1
        elif action[2] == 3:
            noop["sprint"] = 1
        # parse camera pitch
        noop["camera"][0] = float(action[3]) * self._cam_interval + (-180)
        # parse camera yaw
        noop["camera"][1] = float(action[4]) * self._cam_interval + (-180)

        # ------ parse functional actions ------
        fn_action = action[5]
        # note that 0 is no_op
        if fn_action == 0:
            pass
        elif fn_action == 1:
            noop["use"] = 1
        elif fn_action == 2:
            noop["drop"] = 1
        elif fn_action == 3:
            noop["attack"] = 1
        elif fn_action == 4:
            item_to_craft = MC.ALL_CRAFT_SMELT_ITEMS[action[6]]
            if item_to_craft in MC.ALL_HAND_CRAFT_ITEMS_NN_ACTIONS:
                noop["craft"] = item_to_craft
            elif item_to_craft in MC.ALL_TABLE_CRAFT_ONLY_ITEMS_NN_ACTIONS:
                noop["craft_with_table"] = item_to_craft
            elif item_to_craft in MC.ALL_SMELT_ITEMS_NN_ACTIONS:
                noop["smelt"] = item_to_craft
            elif self._strict_check:
                raise ValueError(f"Unknown item {item_to_craft} to craft/smelt!")
        elif fn_action == 5:
            assert action[7] in list(range(MC.N_INV_SLOTS))
            item_id = self._inventory_names[action[7]].replace(" ", "_")
            if item_id == "air":
                if self._strict_check:
                    raise ValueError(
                        "Trying to equip air, raise error with strict check."
                        "You shouldn't execute this action, maybe something wrong with the mask!"
                    )
            else:
                noop["equip"] = item_id
        elif fn_action == 6:
            assert action[7] in list(range(MC.N_INV_SLOTS))
            item_id = self._inventory_names[action[7]].replace(" ", "_")
            if item_id == "air":
                if self._strict_check:
                    raise ValueError(
                        "Trying to place air, raise error with strict check."
                        "You shouldn't execute this action, maybe something wrong with the mask!"
                    )
            else:
                noop["place"] = item_id
        elif fn_action == 7:
            assert action[7] in list(range(MC.N_INV_SLOTS))
            item_id = self._inventory_names[action[7]].replace(" ", "_")
            if item_id == "air":
                if self._strict_check:
                    raise ValueError(
                        "Trying to destroy air, raise error with strict check."
                        "You shouldn't execute this action, maybe something wrong with the mask!"
                    )
            else:
                destroy_item = (True, action[7])
        else:
            raise ValueError(f"Unknown value {fn_action} for function action")
        return noop, destroy_item

    def reverse_action(self, action):
        """
        Malmo action to NN action
        """
        # first convert camera actions to [-pi, +pi]
        action["camera"] = (
            np.arctan2(
                np.sin(action["camera"] * np.pi / 180),
                np.cos(action["camera"] * np.pi / 180),
            )
            * 180
            / np.pi
        )
        assert self.env.action_space.contains(action)

        noop = self.action_space.no_op()
        # ------ parse main actions ------
        # parse forward and back
        if action["forward"] == 1 and action["back"] == 1:
            # cancel each other, noop
            pass
        elif action["forward"] == 1:
            noop[0] = 1
        elif action["back"] == 1:
            noop[0] = 2
        # parse left and right
        if action["left"] == 1 and action["right"] == 1:
            # cancel each other, noop
            pass
        elif action["left"] == 1:
            noop[1] = 1
        elif action["right"] == 1:
            noop[1] = 2
        # parse jump, sneak, sprint
        # prioritize jump
        if action["jump"] == 1:
            noop[2] = 1
        else:
            if action["sneak"] == 1 and action["sprint"] == 1:
                # cancel each other, noop
                pass
            elif action["sneak"] == 1:
                noop[2] = 2
            elif action["sprint"] == 1:
                noop[2] = 3
        # parse camera pitch
        noop[3] = math.ceil((action["camera"][0] - (-180)) / self._cam_interval)
        # parse camera yaw
        noop[4] = math.ceil((action["camera"][1] - (-180)) / self._cam_interval)

        # ------ parse functional actions ------
        # order: attack > use > craft > equip > place > drop > destroy
        if action["attack"] == 1:
            noop[5] = 3
        elif action["use"] == 1:
            noop[5] = 1
        elif action["craft"] != "none" and action["craft"] != 0:
            craft = action["craft"]
            if isinstance(craft, int):
                craft = MC.ALL_PERSONAL_CRAFTING_ITEMS[craft - 1]
            noop[5] = 4
            noop[6] = MC.ALL_CRAFT_SMELT_ITEMS.index(craft)
        elif action["craft_with_table"] != "none" and action["craft_with_table"] != 0:
            craft = action["craft_with_table"]
            if isinstance(craft, int):
                craft = MC.ALL_CRAFTING_TABLE_ITEMS[craft - 1]
            noop[5] = 4
            noop[6] = MC.ALL_CRAFT_SMELT_ITEMS.index(craft)
        elif action["smelt"] != "none" and action["smelt"] != 0:
            smelt = action["smelt"]
            if isinstance(smelt, int):
                smelt = MC.ALL_SMELTING_ITEMS[smelt - 1]
            noop[5] = 4
            noop[6] = MC.ALL_CRAFT_SMELT_ITEMS.index(smelt)
        elif action["equip"] != "none" and action["equip"] != 0:
            equip = action["equip"]
            if isinstance(equip, int):
                equip = MC.ALL_ITEMS[equip - 1]
            equip = equip.replace("_", " ")
            if equip not in self._inventory_names:
                if self._strict_check:
                    raise ValueError(
                        f"try to equip {equip}, but it is not in the inventory {self._inventory_names}"
                    )
            else:
                slot_idx = np.where(self._inventory_names == equip)[0][0]
                noop[5] = 5
                noop[7] = slot_idx
        elif action["place"] != "none" and action["place"] != 0:
            place = action["place"]
            if isinstance(place, int):
                place = MC.ALL_ITEMS[place - 1]
            place = place.replace("_", " ")
            if place not in self._inventory_names:
                if self._strict_check:
                    raise ValueError(
                        f"try to place {place}, but it is not in the inventory {self._inventory_names}"
                    )
            else:
                slot_idx = np.where(self._inventory_names == place)[0][0]
                noop[5] = 6
                noop[7] = slot_idx
        elif action["drop"] == 1:
            noop[5] = 2
        return noop

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        self._inventory_names = obs["inventory"]["name"].copy()
        return obs

    def step(self, action: Sequence[int]):
        malmo_action, destroy_item = self.action(action)
        destroy_item, destroy_slot = destroy_item
        if destroy_item:
            obs, reward, done, info = self.env.set_inventory(
                inventory_list=[
                    InventoryItem(name="air", slot=destroy_slot, quantity=1, variant=0)
                ],
                action=malmo_action,
            )
        else:
            obs, reward, done, info = self.env.step(malmo_action)

        # handle malmo's lags
        if action[5] in {2, 4, 5, 6, 7}:
            for _ in range(2):
                obs, reward, done, info = self.env.step(self.env.action_space.no_op())
        self._inventory_names = obs["inventory"]["name"].copy()
        return obs, reward, done, info
