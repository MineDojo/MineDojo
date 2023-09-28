from typing import Union, Optional, List, Dict, Tuple

from .base import MetaTaskBase
from ...sim.inventory import InventoryItem
from .utils import survive_per_day_reward, survive_n_days_reward, time_since_death_check


class SurvivalMeta(MetaTaskBase):
    """
    Class for survival tasks.
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

        initial_weather: If not ``None``, specifies the initial weather.
                Can be one of ``"clear"``, ``"normal"``, ``"rain"``, ``"thunder"``.
                Default: ``None``.

        lidar_rays: Defines the directions and maximum distances of the lidar rays if ``use_lidar`` is ``True``.
                If supplied, should be a list of tuple(pitch, yaw, distance).
                Pitch and yaw are in radians and relative to agent looking vector.
                Default: ``None``.

        per_day_reward: The reward value for each day of survival
                Default: ``1``.

        seed: The seed for an instance's internal generator.
                Default: ``None``.

        sim_name: Name of a simulation instance.
                Default: ``"SurvivalMeta"``.

        start_food: If not ``None``, specifies initial food condition of the agent.
                Default: ``None``.

        start_health: If not ``None``, specifies initial health condition of the agent.
                Default: ``None``.

        start_position: If not ``None``, specifies the agent's initial location and orientation in the minecraft world.
                Default: ``None``.

        success_reward: The final reward value if survived target days.
                Default: ``None``.

        target_days: Target days to survive.

        use_lidar: If ``True``, includes lidar in observations.
                Default: ``False``.

        use_voxel: If ``True``, includes voxel in observations.
                Default: ``False``.

        voxel_size: Defines the voxel's range in each axis if ``use_voxel`` is ``True``.
                If supplied, should be a dict with keys ``xmin``, ``xmax``, ``ymin``, ``ymax``, ``zmin``, ``zmax``.
                Each value specifies the voxel size relative to the agent.
                Default: ``None``.

        world_seed: Seed for deterministic world generation
                if ``generate_world_type`` is ``"default"`` or ``"specified_biome"``.
                See `here <https://minecraft.wiki/w/Seed_(level_generation)>`_ for more details.
                Default: ``None``.
    """

    _prompt_template = "Survive for {target} days."

    # https://minecraft.fandom.com/el/wiki/Day-night_cycle
    mc_ticks_per_day = 24000

    def __init__(
        self,
        *,
        # ------ target days and reward per day
        target_days: int,
        per_day_reward: Union[int, float] = 1,
        success_reward: Optional[Union[int, float]] = None,
        # ------ initial conditions ------
        start_position: Optional[Dict[str, Union[float, int]]] = None,
        start_health: Optional[float] = None,
        start_food: Optional[int] = None,
        initial_weather: Optional[str] = None,
        initial_inventory: Optional[List[InventoryItem]] = None,
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
        sim_name: str = "SurvivalMeta",
    ):
        assert (
            target_days > 1
        ), f"expect target_days > 1 for non-trivial survival task, got {target_days}"
        self._target_days = target_days
        success_reward = success_reward or target_days * per_day_reward

        reward_fns = [
            survive_per_day_reward(self.mc_ticks_per_day, per_day_reward),
            survive_n_days_reward(self.mc_ticks_per_day, target_days, success_reward),
        ]
        success_criteria = [time_since_death_check(self.mc_ticks_per_day * target_days)]

        super().__init__(
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
        return super().get_prompt(target=self._target_days)
