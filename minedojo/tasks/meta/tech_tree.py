from __future__ import annotations

from typing import Union, Dict, Optional, Tuple, List

from .base import ExtraSpawnMetaTaskBase
from ...sim.inventory import InventoryItem
from .extra_spawn import SpawnItem2Condition
from .utils import (
    always_satisfy_condition,
    use_all_item_check,
    use_any_item_reward,
    simple_inventory_based_reward,
)


ALL_TECH_LEVELS = [
    "wooden",
    "leather",
    "chainmail",
    "golden",
    "stone",
    "iron",
    "diamond",
    "archery",
    "explosives",
    "redstone",
]
ARMORS = ["boots", "chestplate", "helmet", "leggings"]
TOOLS = ["axe", "hoe", "pickaxe", "shovel", "sword"]
TECH_ITEMS = {
    "wooden": [f"wooden_{tool}" for tool in TOOLS],
    "leather": [f"leather_{armor}" for armor in ARMORS],
    "chainmail": [f"chainmail_{armor}" for armor in ARMORS],
    "golden": [f"golden_{item}" for item in ARMORS + TOOLS],
    "stone": [f"stone_{tool}" for tool in TOOLS],
    "iron": [f"iron_{item}" for item in ARMORS + TOOLS],
    "diamond": [f"diamond_{item}" for item in ARMORS + TOOLS],
    "archery": ["bow"],
    "explosives": ["tnt"],
    "redstone": [
        "redstone_block",
        "clock",
        "compass",
        "dispenser",
        "dropper",
        "observer",
        "piston",
        "redstone_lamp",
        "redstone_torch",
        "repeater",
        "detector_rail",
        "comparator",
        "activator_rail",
    ],
}
TECH_ITEMS_FLATTENED = [item for level in TECH_ITEMS.values() for item in level]


class TechTreeMeta(ExtraSpawnMetaTaskBase):
    """
    Class for tech tree tasks.
    Args:
        break_speed_multiplier: Controls the speed of breaking blocks. A value larger than 1.0 accelerates the breaking.
                Default: ``1.0``.

        event_level_control: If ``True``, the agent is able to perform high-level controls including place and equip.
                If ``False``, then is keyboard-mouse level control.
                Default: ``True``.

        fast_reset: If ``True``, reset using MC native command `/kill`, instead of waiting for re-generating new worlds.
            Default: ``True``.

            .. warning::
                Side effects:

                1. Changes to the world will not be reset. E.g., if the agent chops lots of trees then calling
                fast reset will not restore those trees.

                2. If you specify agent starting health and food, these specs will only be respected at the first reset
                (i.e., generating a new world) but will not be respected in the following resets (i.e., reset using MC cmds).
                So be careful to use this wrapper if your usages require specific initial health/food.

                3. Statistics/achievements will not be reset. This wrapper will maintain a property ``info_prev_reset``.
                If your tasks use stat/achievements to evaluation, please retrieve this property and compute differences.

        image_size: The size of image observations.

        initial_mobs: The types of mobs that are spawned initially.
                Default: ``None``.

        initial_mob_spawn_range_high: The upperbound on each horizontal axis from the center of the area to spawn initially.
                Default: ``None``.

        initial_mob_spawn_range_low: The lowerbound on each horizontal axis from the center of the area to spawn initially.
                Default: ``None``.

        initial_weather: If not ``None``, specifies the initial weather.
                Can be one of ``"clear"``, ``"normal"``, ``"rain"``, ``"thunder"``.
                Default: ``None``.

        lidar_rays: Defines the directions and maximum distances of the lidar rays if ``use_lidar`` is ``True``.
                If supplied, should be a list of tuple(pitch, yaw, distance).
                Pitch and yaw are in radians and relative to agent looking vector.
                Default: ``None``.

        obtain_items_reward_weights: The reward values of obtaining necessary items for unlocking the target tech.
                Default: ``1.0``.

        seed: The seed for an instance's internal generator.
                Default: ``None``.

        sim_name: Name of a simulation instance.
                Default: ``"TechTreeMeta"``.

        spawn_range_high: The upperbound on each horizontal axis from the center of the area to spawn
                Default: ``None``.

        spawn_range_low: The lowerbound on each horizontal axis from the center of the area to spawn
                Default: ``None``.

        spawn_rate: The probability of spawning in each step.
                Default: ``None``.

        start_food: If not ``None``, specifies initial food condition of the agent.
                Default: ``None``.

        start_health: If not ``None``, specifies initial health condition of the agent.
                Default: ``None``.

        start_position: If not ``None``, specifies the agent's initial location and orientation in the minecraft world.
                Default: ``None``.

        tech: Target tech to be unlocked.

        use_lidar: If ``True``, includes lidar in observations.
                Default: ``False``.

        use_items_reward_weights: The reward value of using the items, which is the last step of unlocking a tech.
                Default: ``10.0``.

        use_voxel: If ``True``, includes voxel in observations.
                Default: ``False``.

        voxel_size: Defines the voxel's range in each axis if ``use_voxel`` is ``True``.
                If supplied, should be a dict with keys ``xmin``, ``xmax``, ``ymin``, ``ymax``, ``zmin``, ``zmax``.
                Each value specifies the voxel size relative to the agent.
                Default: ``None``.

        world_seed: Seed for deterministic world generation
                if ``generate_world_type`` is ``"default"`` or ``"specified_biome"``.
                See `here <https://minecraft.fandom.com/wiki/Seed_(level_generation)>`_ for more details.
                Default: ``None``.
    """

    _prompt_template = "Unlock {tech} technology."

    def __init__(
        self,
        *,
        # ------ target technology ------
        tech: str | None = None,
        tech_item: str | None = None,
        obtain_items_reward_weights: Union[
            int, float, Dict[str, Union[int, float]]
        ] = 1.0,
        use_items_reward_weights: Union[
            int, float, Dict[str, Union[int, float]]
        ] = 10.0,
        # ------ initial & extra spawn control ------
        initial_mobs: Optional[Union[str, List[str]]] = None,
        initial_mob_spawn_range_low: Optional[Tuple[int, int, int]] = None,
        initial_mob_spawn_range_high: Optional[Tuple[int, int, int]] = None,
        spawn_rate: Optional[Dict[str, Union[float, int]]] = None,
        spawn_range_low: Optional[Tuple[int, int, int]] = None,
        spawn_range_high: Optional[Tuple[int, int, int]] = None,
        # ------ initial conditions ------
        initial_inventory: Optional[List[InventoryItem]] = None,
        start_position: Optional[Dict[str, Union[float, int]]] = None,
        start_health: Optional[float] = None,
        start_food: Optional[int] = None,
        initial_weather: Optional[str] = None,
        # ------ global conditions ------
        break_speed_multiplier: float = 1.0,
        # ------ sim seed & world seed ------
        seed: Optional[int] = None,
        world_seed: Optional[str] = None,
        # ------ reset mode ------
        fast_reset: bool = True,
        # ------ obs ------
        image_size: Union[int, Tuple[int, int]],
        use_voxel: bool = False,
        voxel_size: Optional[Dict[str, int]] = None,
        use_lidar: bool = False,
        lidar_rays: Optional[List[Tuple[float, float, float]]] = None,
        # ------ event-level action or keyboard-mouse level action ------
        event_level_control: bool = True,
        # ------ misc ------
        sim_name: str = "TechTreeMeta",
    ):
        # should provide `tech` or `tech_item`, but not both
        assert (tech is not None or tech_item is not None) and (
            tech is None or tech_item is None
        ), "should provide `tech` or `tech_item`, but not both"

        if tech is not None:
            assert (
                tech in ALL_TECH_LEVELS
            ), f"Invalid target tech: {tech}, expect one from {ALL_TECH_LEVELS}"
            self._target_tech = tech
            tech_items = TECH_ITEMS[tech]
        else:
            assert tech_item in TECH_ITEMS_FLATTENED
            self._target_tech = tech_item.replace("_", " ")
            tech_items = [tech_item]
        if isinstance(obtain_items_reward_weights, int) or isinstance(
            obtain_items_reward_weights, float
        ):
            obtain_items_reward_weights = {
                item: obtain_items_reward_weights for item in tech_items
            }
        elif isinstance(obtain_items_reward_weights, dict):
            assert set(obtain_items_reward_weights.keys()) == set(
                tech_items
            ), f"{set(obtain_items_reward_weights.keys())} must match {set(tech_items)}"
        if isinstance(use_items_reward_weights, int) or isinstance(
            use_items_reward_weights, float
        ):
            use_items_reward_weights = {
                item: use_items_reward_weights for item in tech_items
            }
        elif isinstance(use_items_reward_weights, dict):
            assert set(use_items_reward_weights.keys()) == set(
                tech_items
            ), f"{set(use_items_reward_weights.keys())} must match {set(tech_items)}"

        spawn_condition = None
        if spawn_rate is not None:
            assert isinstance(spawn_rate, dict), (
                f"in TechTree you must explicitly provide spawn items and rates by passing a dict, "
                f"but got {type(spawn_rate)}"
            )
            spawn_condition = {
                k: SpawnItem2Condition.get(k, always_satisfy_condition)
                for k in spawn_rate.keys()
            }

        # use any target items only *once* can succeed
        success_criteria = [use_all_item_check({k: 1 for k in tech_items})]
        reward_fns = [
            # rewards for obtaining target items
            simple_inventory_based_reward(name=k, weight=v)
            for k, v in obtain_items_reward_weights.items()
        ] + [
            # rewards for using target items
            use_any_item_reward(use_items_reward_weights)
        ]

        super().__init__(
            initial_mobs=initial_mobs,
            initial_mob_spawn_range_low=initial_mob_spawn_range_low,
            initial_mob_spawn_range_high=initial_mob_spawn_range_high,
            extra_spawn_rate=spawn_rate,
            extra_spawn_condition=spawn_condition,
            extra_spawn_range_low=spawn_range_low,
            extra_spawn_range_high=spawn_range_high,
            fast_reset=fast_reset,
            success_criteria=success_criteria,
            reward_fns=reward_fns,
            seed=seed,
            sim_name=sim_name,
            image_size=image_size,
            use_voxel=use_voxel,
            voxel_size=voxel_size,
            use_lidar=use_lidar,
            lidar_rays=lidar_rays,
            event_level_control=event_level_control,
            initial_inventory=initial_inventory,
            break_speed_multiplier=break_speed_multiplier,
            world_seed=world_seed,
            start_position=start_position,
            initial_weather=initial_weather,
            start_health=start_health,
            start_food=start_food,
        )

    @property
    def task_prompt(self) -> str:
        return super().get_prompt(tech=self._target_tech)
