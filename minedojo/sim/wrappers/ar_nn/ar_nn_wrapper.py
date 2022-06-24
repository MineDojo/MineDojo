from typing import Union, Optional

import gym

from .ar_masks_wrapper import ARMasksWrapper as _ARMasksWrapper
from .nn_action_space_wrapper import NNActionSpaceWrapper as _NNActionSpaceWrapper
from .delta_inventory_wrapper import DeltaInventoryWrapper as _DeltaInventoryObsWrapper


class ARNNWrapper(gym.Wrapper):
    def __init__(
        self,
        sim,
        cam_interval: Union[int, float] = 15,
        strict_check: bool = True,
        op_action_idx: int = 5,
        craft_action_idx: int = 4,
        craft_arg_idx: int = 6,
        n_increased: int = 1,
        n_decreased: int = 4,
        default_item_name: str = "air",
        action_categories_and_num_args: Optional[dict[str, int]] = None,
    ):
        sim = _DeltaInventoryObsWrapper(
            _ARMasksWrapper(
                _NNActionSpaceWrapper(
                    env=sim,
                    discretized_camera_interval=cam_interval,
                    strict_check=strict_check,
                ),
                action_categories_and_num_args=action_categories_and_num_args,
            ),
            op_action_idx=op_action_idx,
            craft_action_idx=craft_action_idx,
            craft_arg_idx=craft_arg_idx,
            n_increased=n_increased,
            n_decreased=n_decreased,
            default_item_name=default_item_name,
        )
        self.cam_interval = cam_interval
        super().__init__(env=sim)

    def reverse_action(self, action):
        return self.env.env.env.reverse_action(action)
