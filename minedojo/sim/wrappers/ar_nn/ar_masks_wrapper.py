from typing import Any, Union, Optional

import gym
import numpy as np

from ...sim import MineDojoSim
from ....sim import spaces as spaces
from ....sim.mc_meta import mc as MC
from ..utils import get_recipes_matrix, get_inventory_vector


class ARMasksWrapper(gym.ObservationWrapper):
    def __init__(
        self,
        env: Union[MineDojoSim, gym.Wrapper],
        action_categories_and_num_args: Optional[dict[str, int]] = None,
    ):
        assert "inventory" in env.observation_space.keys()
        assert "nearby_tools" in env.observation_space.keys()
        assert "table" in env.observation_space["nearby_tools"].keys()
        assert "furnace" in env.observation_space["nearby_tools"].keys()
        assert isinstance(
            env.action_space, spaces.MultiDiscrete
        ), "please use this wrapper with `NNActionSpaceWrapper!`"
        assert (
            len(env.action_space.nvec) == 8
        ), "please use this wrapper with `NNActionSpaceWrapper!`"
        super().__init__(env=env)

        action_categories_and_num_args = action_categories_and_num_args or dict(
            no_op=0, use=0, drop=0, attack=0, craft=1, equip=1, place=1, destroy=1
        )
        obs_space = env.observation_space
        n_fn_actions = len(action_categories_and_num_args)
        obs_space["masks"] = spaces.Dict(
            {
                "action_type": spaces.Box(
                    low=0, high=1, shape=(n_fn_actions,), dtype=bool
                ),
                "action_arg": spaces.Box(
                    low=0, high=1, shape=(n_fn_actions, 1), dtype=bool
                ),
                "equip": spaces.Box(low=0, high=1, shape=(MC.N_INV_SLOTS,), dtype=bool),
                "place": spaces.Box(low=0, high=1, shape=(MC.N_INV_SLOTS,), dtype=bool),
                "destroy": spaces.Box(
                    low=0, high=1, shape=(MC.N_INV_SLOTS,), dtype=bool
                ),
                "craft_smelt": spaces.Box(
                    low=0, high=1, shape=(len(MC.ALL_CRAFT_SMELT_ITEMS),), dtype=bool
                ),
            }
        )
        # remove `full_stats`
        if "full_stats" in obs_space.keys():
            del obs_space["full_stats"]
        self.observation_space = obs_space
        # a_arg_mask can be determined now and will not change
        self._a_arg_mask = np.array(
            list(action_categories_and_num_args.values()), dtype=bool
        )[..., np.newaxis]
        self._a_cats = list(action_categories_and_num_args.keys())
        self._n_fn_actions = n_fn_actions
        # no_op, use, and attack are always valid
        self._a_cat_always_true_indices = np.isin(
            np.array(self._a_cats), np.array(["no_op", "use", "attack"])
        ).nonzero()[0]
        self._equip_place_destroy_indices = np.isin(
            np.array(self._a_cats), np.array(["equip", "place", "destroy"])
        ).nonzero()[0]
        # get recipe matrix
        self._recipes = get_recipes_matrix()

    def observation(self, observation: dict[str, Any]):
        # ------ craft smelt mask ------
        inventory_vector = get_inventory_vector(observation["inventory"])
        craft_smelt_mask = ~np.any(
            (inventory_vector - self._recipes) < 0, axis=1
        ).astype(
            bool
        )  # (N_all_craftable)
        # meta mask using `nearby_table` and `nearby_furnace`
        nearby_table, nearby_furnace = (
            observation["nearby_tools"]["table"],
            observation["nearby_tools"]["furnace"],
        )
        nearby_table = np.array(
            [nearby_table] * len(MC.ALL_TABLE_CRAFT_ONLY_ITEMS_NN_ACTIONS), dtype=bool
        )
        nearby_furnace = np.array(
            [nearby_furnace] * len(MC.ALL_SMELT_ITEMS_NN_ACTIONS), dtype=bool
        )
        table_craft_items_indices = slice(
            len(MC.ALL_HAND_CRAFT_ITEMS_NN_ACTIONS),
            len(MC.ALL_HAND_CRAFT_ITEMS_NN_ACTIONS)
            + len(MC.ALL_TABLE_CRAFT_ONLY_ITEMS_NN_ACTIONS),
        )
        craft_smelt_mask[table_craft_items_indices] = np.logical_and(
            nearby_table, craft_smelt_mask[table_craft_items_indices]
        )
        craft_smelt_mask[-len(MC.ALL_SMELT_ITEMS_NN_ACTIONS) :] = np.logical_and(
            nearby_furnace, craft_smelt_mask[-len(MC.ALL_SMELT_ITEMS_NN_ACTIONS) :]
        )
        # ------ determine destroy mask ------
        # destroy mask is simply if slots are occupied
        destroy_mask = (observation["inventory"]["name"] != "air").astype(bool)
        # ------ determine place mask ------
        # True if that slot is occupied by placeable items
        place_mask = np.logical_and(
            (observation["inventory"]["name"] != "air").astype(bool),
            np.isin(
                observation["inventory"]["name"], np.array(MC.PLACEABLE_ITEM_NAMES)
            ),
        )
        # ------ determine equip mask
        # True if that slot is occupied
        # special treat for main-hand slot
        equip_mask = (observation["inventory"]["name"] != "air").astype(bool)
        equip_mask[0] = (
            equip_mask[0]
            and observation["inventory"]["name"][0] in MC.NON_MAINHAND_ITEM_NAMES
        )

        # ------ determine action category mask ------
        a_cat_mask = np.empty(shape=(self._n_fn_actions,), dtype=bool)
        # no_op, use, and attack are always valid
        a_cat_mask[self._a_cat_always_true_indices] = True
        # validity of drop is dependent on if anything held in the main-hand
        a_cat_mask[self._a_cats.index("drop")] = (
            False if observation["inventory"]["name"][0] == "air" else True
        )
        # validity of craft equals to any(craft_smelt_mask) and the inventory is not full
        a_cat_mask[self._a_cats.index("craft")] = np.any(
            craft_smelt_mask
        ) and not np.all((observation["inventory"]["name"] != "air").astype(bool))
        # validity of equip simply equals to any(equip_mask)
        a_cat_mask[self._a_cats.index("equip")] = np.any(equip_mask)
        # validity of place simply equals to any(place_mask)
        a_cat_mask[self._a_cats.index("place")] = np.any(place_mask)
        # validity of destroy simple equals to any(destroy_mask)
        a_cat_mask[self._a_cats.index("destroy")] = np.any(destroy_mask)

        observation["masks"] = {
            "action_type": a_cat_mask,
            "action_arg": self._a_arg_mask,
            "equip": equip_mask,
            "place": place_mask,
            "destroy": destroy_mask,
            "craft_smelt": craft_smelt_mask,
        }
        # remove `full_stats`
        if "full_stats" in observation:
            del observation["full_stats"]
        return observation
