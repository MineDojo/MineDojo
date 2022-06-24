from typing import Union
from copy import deepcopy
from collections import deque

import gym
import numpy as np

from ..utils import *
from ...sim import MineDojoSim
from ....sim import spaces as spaces
from ....sim.mc_meta import mc as MC


ALL_ITEMS = np.array(MC.ALL_ITEMS)


class DeltaInventoryWrapper(gym.Wrapper):
    def __init__(
        self,
        env: Union[MineDojoSim, gym.Wrapper],
        op_action_idx: int = 5,
        craft_action_idx: int = 4,
        craft_arg_idx: int = 6,
        n_increased: int = 1,
        n_decreased: int = 4,
        default_item_name: str = "air",
    ):
        assert "inventory" in env.observation_space.keys()
        assert "masks" in env.observation_space.keys()
        assert "craft_smelt" in env.observation_space["masks"].keys()
        assert isinstance(
            env.action_space, spaces.MultiDiscrete
        ), "please use this wrapper with `NNActionSpaceWrapper!`"
        assert (
            len(env.action_space.nvec) == 8
        ), "please use this wrapper with `NNActionSpaceWrapper!`"
        assert op_action_idx < len(env.action_space.nvec)
        assert craft_arg_idx < len(env.action_space.nvec)
        super().__init__(env=env)
        obs_space = env.observation_space
        obs_space["delta_inv"] = spaces.Dict(
            {
                "inc_name_by_craft": spaces.Text(shape=(n_increased,)),
                "inc_quantity_by_craft": spaces.Box(
                    low=0, high=64, shape=(n_increased,), dtype=np.float32
                ),
                "dec_name_by_craft": spaces.Text(shape=(n_decreased,)),
                "dec_quantity_by_craft": spaces.Box(
                    low=0, high=64, shape=(n_decreased,), dtype=np.float32
                ),
                "inc_name_by_other": spaces.Text(shape=(n_increased,)),
                "inc_quantity_by_other": spaces.Box(
                    low=0, high=64, shape=(n_increased,), dtype=np.float32
                ),
                "dec_name_by_other": spaces.Text(shape=(n_decreased,)),
                "dec_quantity_by_other": spaces.Box(
                    low=0, high=64, shape=(n_decreased,), dtype=np.float32
                ),
            }
        )
        self.observation_space = obs_space
        self._default_item_name = default_item_name
        self._n_increased = n_increased
        self._n_decreased = n_decreased
        self._op_action_idx = op_action_idx
        self._craft_action_idx = craft_action_idx
        self._craft_arg_idx = craft_arg_idx

        self._recipes = get_recipes_matrix()
        self._prev_inventory = None
        self._prev_mask = None
        # note that there is two-step lag between executing a crafting action
        # and that item really goes into the inventory
        # so we use a deque with len=3 to cache the history action
        self._prev_craft_actions = deque(maxlen=1)

    def reset(self, **kwargs):
        observation = self.env.reset(**kwargs)
        self._prev_inventory = deepcopy(observation["inventory"])
        self._prev_mask = deepcopy(observation["masks"]["craft_smelt"])
        self._prev_craft_actions = deque(maxlen=1)
        return self.observation(observation, None)

    def step(self, action):
        observation, reward, done, info = self.env.step(action)
        new_obs = self.observation(observation, action)
        self._prev_inventory = deepcopy(observation["inventory"])
        self._prev_mask = deepcopy(observation["masks"]["craft_smelt"])
        return new_obs, reward, done, info

    def observation(self, observation, action):
        if action is None:
            # first step
            delta_obs = {
                "inc_name_by_craft": np.array(
                    [self._default_item_name] * self._n_increased
                ),
                "inc_quantity_by_craft": np.zeros(
                    (self._n_increased,), dtype=np.float32
                ),
                "dec_name_by_craft": np.array(
                    [self._default_item_name] * self._n_decreased
                ),
                "dec_quantity_by_craft": np.zeros(
                    (self._n_decreased,), dtype=np.float32
                ),
                "inc_name_by_other": np.array(
                    [self._default_item_name] * self._n_increased
                ),
                "inc_quantity_by_other": np.zeros(
                    (self._n_increased,), dtype=np.float32
                ),
                "dec_name_by_other": np.array(
                    [self._default_item_name] * self._n_decreased
                ),
                "dec_quantity_by_other": np.zeros(
                    (self._n_decreased,), dtype=np.float32
                ),
            }
        else:
            new_craft_idx = (
                None
                if action[self._op_action_idx] != self._craft_action_idx
                else action[self._craft_arg_idx]
            )
            self._prev_craft_actions.append(new_craft_idx)
            craft_idx = self._prev_craft_actions[0]
            cur_inv_vector = get_inventory_vector(observation["inventory"])[0]
            pre_inv_vector = get_inventory_vector(self._prev_inventory)[0]
            delta_inv_vector = cur_inv_vector - pre_inv_vector
            increment_indices = np.flatnonzero(delta_inv_vector > 0)[
                : self._n_increased
            ]
            decrement_indices = np.flatnonzero(delta_inv_vector < 0)[
                : self._n_decreased
            ]

            delta_obs = {}
            if len(increment_indices) == 0:
                # no increment
                delta_obs.update(
                    {
                        "inc_name_by_craft": np.array(
                            [self._default_item_name] * self._n_increased
                        ),
                        "inc_quantity_by_craft": np.zeros(
                            (self._n_increased,), dtype=np.float32
                        ),
                        "inc_name_by_other": np.array(
                            [self._default_item_name] * self._n_increased
                        ),
                        "inc_quantity_by_other": np.zeros(
                            (self._n_increased,), dtype=np.float32
                        ),
                    }
                )
            else:
                # "craft" is not selected!
                if craft_idx is None:
                    delta_obs.update(
                        {
                            "inc_name_by_craft": np.array(
                                [self._default_item_name] * self._n_increased
                            ),
                            "inc_quantity_by_craft": np.zeros(
                                (self._n_increased,), dtype=np.float32
                            ),
                            "inc_name_by_other": np.concatenate(
                                (
                                    ALL_ITEMS[increment_indices],
                                    np.array(
                                        [self._default_item_name]
                                        * (self._n_increased - len(increment_indices))
                                    ),
                                )
                            ),
                            "inc_quantity_by_other": np.concatenate(
                                (
                                    delta_inv_vector[increment_indices],
                                    np.zeros(
                                        shape=(
                                            self._n_increased - len(increment_indices),
                                        )
                                    ),
                                )
                            ).astype(np.float32),
                        }
                    )
                else:
                    item_name_to_craft = MC.ALL_CRAFT_SMELT_ITEMS[craft_idx]
                    item_idx_to_craft = MC.ALL_ITEMS.index(item_name_to_craft)
                    if (
                        bool(self._prev_mask[craft_idx]) is True
                        and item_idx_to_craft in increment_indices
                    ):
                        delta_obs.update(
                            {
                                "inc_name_by_craft": np.concatenate(
                                    (
                                        ALL_ITEMS[increment_indices],
                                        np.array(
                                            [self._default_item_name]
                                            * (
                                                self._n_increased
                                                - len(increment_indices)
                                            )
                                        ),
                                    )
                                ),
                                "inc_quantity_by_craft": np.concatenate(
                                    (
                                        delta_inv_vector[increment_indices],
                                        np.zeros(
                                            shape=(
                                                self._n_increased
                                                - len(increment_indices),
                                            )
                                        ),
                                    )
                                ).astype(np.float32),
                                "inc_name_by_other": np.array(
                                    [self._default_item_name] * self._n_increased
                                ),
                                "inc_quantity_by_other": np.zeros(
                                    (self._n_increased,), dtype=np.float32
                                ),
                            }
                        )
                    else:
                        delta_obs.update(
                            {
                                "inc_name_by_craft": np.array(
                                    [self._default_item_name] * self._n_increased
                                ),
                                "inc_quantity_by_craft": np.zeros(
                                    (self._n_increased,), dtype=np.float32
                                ),
                                "inc_name_by_other": np.concatenate(
                                    (
                                        ALL_ITEMS[increment_indices],
                                        np.array(
                                            [self._default_item_name]
                                            * (
                                                self._n_increased
                                                - len(increment_indices)
                                            )
                                        ),
                                    )
                                ),
                                "inc_quantity_by_other": np.concatenate(
                                    (
                                        delta_inv_vector[increment_indices],
                                        np.zeros(
                                            shape=(
                                                self._n_increased
                                                - len(increment_indices),
                                            )
                                        ),
                                    )
                                ).astype(np.float32),
                            }
                        )
            if len(decrement_indices) == 0:
                # no decrement
                delta_obs.update(
                    {
                        "dec_name_by_craft": np.array(
                            [self._default_item_name] * self._n_decreased
                        ),
                        "dec_quantity_by_craft": np.zeros(
                            (self._n_decreased,), dtype=np.float32
                        ),
                        "dec_name_by_other": np.array(
                            [self._default_item_name] * self._n_decreased
                        ),
                        "dec_quantity_by_other": np.zeros(
                            (self._n_decreased,), dtype=np.float32
                        ),
                    }
                )
            else:
                # "craft" is not selected!
                if craft_idx is None:
                    delta_obs.update(
                        {
                            "dec_name_by_craft": np.array(
                                [self._default_item_name] * self._n_decreased
                            ),
                            "dec_quantity_by_craft": np.zeros(
                                (self._n_decreased,), dtype=np.float32
                            ),
                            "dec_name_by_other": np.concatenate(
                                (
                                    ALL_ITEMS[decrement_indices],
                                    np.array(
                                        [self._default_item_name]
                                        * (self._n_decreased - len(decrement_indices))
                                    ),
                                )
                            ),
                            "dec_quantity_by_other": abs(
                                np.concatenate(
                                    (
                                        delta_inv_vector[decrement_indices],
                                        np.zeros(
                                            (
                                                self._n_decreased
                                                - len(decrement_indices),
                                            )
                                        ),
                                    )
                                ).astype(np.float32)
                            ),
                        }
                    )
                else:
                    ingredients_indices = np.flatnonzero(self._recipes[craft_idx] > 0)
                    if bool(self._prev_mask[craft_idx]) is True and set(
                        ingredients_indices
                    ).issubset(set(decrement_indices)):
                        delta_obs.update(
                            {
                                "dec_name_by_craft": np.concatenate(
                                    (
                                        ALL_ITEMS[decrement_indices],
                                        np.array(
                                            [self._default_item_name]
                                            * (
                                                self._n_decreased
                                                - len(decrement_indices)
                                            )
                                        ),
                                    )
                                ),
                                "dec_quantity_by_craft": abs(
                                    np.concatenate(
                                        (
                                            delta_inv_vector[decrement_indices],
                                            np.zeros(
                                                (
                                                    self._n_decreased
                                                    - len(decrement_indices),
                                                )
                                            ),
                                        )
                                    ).astype(np.float32)
                                ),
                                "dec_name_by_other": np.array(
                                    [self._default_item_name] * self._n_decreased
                                ),
                                "dec_quantity_by_other": np.zeros(
                                    (self._n_decreased,), dtype=np.float32
                                ),
                            }
                        )
                    else:
                        delta_obs.update(
                            {
                                "dec_name_by_craft": np.array(
                                    [self._default_item_name] * self._n_decreased
                                ),
                                "dec_quantity_by_craft": np.zeros(
                                    (self._n_decreased,), dtype=np.float32
                                ),
                                "dec_name_by_other": np.concatenate(
                                    (
                                        ALL_ITEMS[decrement_indices],
                                        np.array(
                                            [self._default_item_name]
                                            * (
                                                self._n_decreased
                                                - len(decrement_indices)
                                            )
                                        ),
                                    )
                                ),
                                "dec_quantity_by_other": abs(
                                    np.concatenate(
                                        (
                                            delta_inv_vector[decrement_indices],
                                            np.zeros(
                                                (
                                                    self._n_decreased
                                                    - len(decrement_indices),
                                                )
                                            ),
                                        )
                                    ).astype(np.float32)
                                ),
                            }
                        )
        observation["delta_inv"] = delta_obs
        return observation
