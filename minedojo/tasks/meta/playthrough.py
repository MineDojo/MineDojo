from typing import Optional, Union, List, Dict, Tuple

from .base import MetaTaskBase
from ...sim.inventory import InventoryItem
from .utils import simple_inventory_based_check, possess_item_reward


# A human beginner takes 8 hours to defeat the dragon. Each second includes four actions.
TIME_LIMIT = int(8 * 3600 * 4)


class Playthrough(MetaTaskBase):
    """
    Class for the playthrough tasks.
    Args:
        always_night: If ``True``, the world will always be at night.
                Default: ``False``.

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

        obtain_dragon_egg_reward: The reward value of obtaining the dragon egg.
                The dragon egg can be solely obtained by successfully defeating the ender dragon.
                So it serves as a proxy for playing through the vanilla game.
                Default: ``10``.

        seed: The seed for an instance's internal generator.
                Default: ``None``.

        sim_name: Name of a simulation instance.
                Default: ``"Playthrough"``.

        start_at_night: If ``True``, the task starts at night.
                Default: ``True``.

        start_food: If not ``None``, specifies initial food condition of the agent.
                Default: ``None``.

        start_health: If not ``None``, specifies initial health condition of the agent.
                Default: ``None``.

        start_position: If not ``None``, specifies the agent's initial location and orientation in the minecraft world.
                Default: ``None``.

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
                See `here <https://minecraft.fandom.com/wiki/Seed_(level_generation)>`_ for more details.
                Default: ``None``.
    """

    _prompt_template = "Defeat the Ender Dragon and obtain the trophy dragon egg."

    def __init__(
        self,
        *,
        # ------ reward weights ------
        obtain_dragon_egg_reward: Union[float, int] = 10,
        # ------ initial conditions ------
        start_position: Optional[Dict[str, Union[float, int]]] = None,
        start_health: Optional[float] = None,
        start_food: Optional[int] = None,
        start_at_night: bool = False,
        always_night: bool = False,
        initial_weather: Optional[str] = None,
        initial_inventory: Optional[List[InventoryItem]] = None,
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
        break_speed_multiplier: float = 1.0,
        sim_name: str = "Playthrough",
    ):
        success_criteria = [simple_inventory_based_check(name="dragon_egg", quantity=1)]
        reward_fns = [
            possess_item_reward(
                name="dragon_egg", quantity=1, weight=obtain_dragon_egg_reward
            )
        ]

        start_time, allow_time_passage = None, True
        if start_at_night:
            start_time = 13000
        if always_night:
            start_time = 18000
            allow_time_passage = False

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
            start_time=start_time,
            allow_time_passage=allow_time_passage,
            start_health=start_health,
            start_food=start_food,
        )

        self.time_limit = TIME_LIMIT
        self._elapsed_steps = None

    @property
    def task_prompt(self) -> str:
        return self._prompt_template

    def reset(self, **kwargs):
        self._elapsed_steps = 0
        return self.env.reset(**kwargs)

    def step(self, action):
        assert (
            self._elapsed_steps is not None
        ), "Cannot call env.step() before calling reset()"
        observation, reward, done, info = self.env.step(action)
        self._elapsed_steps += 1
        if self._elapsed_steps >= self._max_episode_steps:
            info["TimeLimit.truncated"] = not done
            done = True
        return observation, reward, done, info
