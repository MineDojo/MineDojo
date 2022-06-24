"""
Execute MineCraft native commands
"""
import logging
from typing import Optional, List, Union

import numpy as np

from .inventory import (
    InventoryItem,
    parse_inventory_item,
    map_slot_number_to_cmd_slot,
)


class CMDExecutor:
    logger = logging.getLogger("cmd_executor")
    valid_cmds = {
        "summon",
        "kill",
        "time",
        "weather",
        "replaceitem",
        "tp",
        "clear",
        "setblock",
        "spreadplayers",
    }

    def __init__(self, world, raise_error_on_invalid_cmds: bool = False):
        # avoid circular import
        from .sim import MineDojoSim

        self._world: MineDojoSim = world
        self._raise_error_on_invalid_cmds = raise_error_on_invalid_cmds
        self._world_action_space = world.action_space

    def execute_cmd(self, cmd: str, action: Optional[dict] = None):
        if (not cmd.startswith("/")) or (cmd.split()[0][1:] not in self.valid_cmds):
            if not self._raise_error_on_invalid_cmds:
                self.logger.warning(f"Invalid cmd {cmd}, skipping...")
                if action is None:
                    return (
                        self._world.prev_obs,
                        0,
                        self._world.is_terminated,
                        self._world.prev_info,
                    )
                else:
                    return self._world.step(action)
            else:
                raise ValueError(f"Invalid cmd {cmd}")
        else:
            action = action or self._world.action_space.no_op()
            action["chat"] = cmd
            return self._world.step(action)

    def spawn_mobs(
        self,
        mobs: Union[str, List[str]],
        rel_positions: Union[np.ndarray, list],
        action: Optional[dict] = None,
    ):
        if isinstance(mobs, str):
            mobs = [mobs]
        if isinstance(rel_positions, list):
            rel_positions = np.array(rel_positions)
        if rel_positions.ndim == 1:
            rel_positions = rel_positions[np.newaxis, ...]
        if len(mobs) > 1 and len(rel_positions) == 1:
            rel_positions = np.repeat(rel_positions, len(mobs), axis=0)
        assert (
            rel_positions.ndim == 2
        ), f"Expect `rel_positions` to be 2 dimensional, but got {rel_positions.ndim} dims"
        assert (
            rel_positions.shape[1] == 3
        ), "Expect `rel_positions` to contain x, y, and z"
        assert len(mobs) == len(
            rel_positions
        ), f"Expect {len(mobs)} relative positions, but got {len(rel_positions)}"

        obs, info = self._world.prev_obs, self._world.prev_info
        for mob, rel_pos in zip(mobs, rel_positions):
            cmd = f"/summon {mob} ~{int(rel_pos[0])} ~{int(rel_pos[1])} ~{int(rel_pos[2])}"
            obs, _, _, info = self.execute_cmd(cmd, action)
        return obs, 0, self._world.is_terminated, info

    def set_block(
        self,
        blocks: Union[str, List[str]],
        rel_positions: Union[np.ndarray, list],
        action: Optional[dict] = None,
    ):
        if isinstance(blocks, str):
            blocks = [blocks]
        if isinstance(rel_positions, list):
            rel_positions = np.array(rel_positions)
        if rel_positions.ndim == 1:
            rel_positions = rel_positions[np.newaxis, ...]
        if len(blocks) > 1 and len(rel_positions) == 1:
            rel_positions = np.repeat(rel_positions, len(blocks), axis=0)
        assert (
            rel_positions.ndim == 2
        ), f"Expect `rel_positions` to be 2 dimensional, but got {rel_positions.ndim} dims"
        assert (
            rel_positions.shape[1] == 3
        ), "Expect `rel_positions` to contain x, y, and z"
        assert len(blocks) == len(
            rel_positions
        ), f"Expect {len(blocks)} relative positions, but got {len(rel_positions)}"

        obs, info = self._world.prev_obs, self._world.prev_info
        for block, rel_pos in zip(blocks, rel_positions):
            cmd = f"/setblock ~{int(rel_pos[0])} ~{int(rel_pos[1])} ~{int(rel_pos[2])} {block}"
            obs, _, _, info = self.execute_cmd(cmd, action)
        return obs, 0, self._world.is_terminated, info

    def clear_inventory(self, action: Optional[dict] = None):
        obs, _, _, info = self.execute_cmd("/clear", action)
        return obs, 0, self._world.is_terminated, info

    def set_inventory(
        self, inventory_list: List[InventoryItem], action: Optional[dict] = None
    ):
        obs, info = self._world.prev_obs, self._world.prev_info
        for inventory_item in inventory_list:
            slot, item_dict = parse_inventory_item(inventory_item)
            obs, _, _, info = self.execute_cmd(
                f'/replaceitem entity @p {map_slot_number_to_cmd_slot(slot)} minecraft:{item_dict["type"]} {item_dict["quantity"]} {item_dict["metadata"]}',
                action,
            )
        return obs, 0, self._world.is_terminated, info

    def teleport_agent(self, x, y, z, yaw, pitch, action: Optional[dict] = None):
        obs, _, _, info = self.execute_cmd(f"/tp {x} {y} {z} {yaw} {pitch}", action)
        return obs, 0, self._world.is_terminated, info

    def kill_agent(self, action: Optional[dict] = None):
        obs, _, _, info = self.execute_cmd("/kill", action)
        return obs, 0, self._world.is_terminated, info

    def set_time(self, time: int, action: Optional[dict] = None):
        obs, _, _, info = self.execute_cmd(f"/time set {time}", action)
        return obs, 0, self._world.is_terminated, info

    def set_weather(self, weather: str, action: Optional[dict] = None):
        obs, _, _, info = self.execute_cmd(f"/weather {weather}", action)
        return obs, 0, self._world.is_terminated, info

    def random_teleport(self, max_range: int, action: Optional[dict] = None):
        obs, _, _, info = self.execute_cmd(
            f"/spreadplayers ~ ~ 0 {max_range} false @p", action
        )
        return obs, 0, self._world.is_terminated, info
