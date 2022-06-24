from functools import partial
from mypy_extensions import Arg
from typing import Union, Callable


__all__ = [
    "extra_spawn_condition_base",
    "always_satisfy_condition",
    "check_below_height_condition",
    "check_above_height_condition",
    "check_below_light_level_condition",
    "check_above_light_level_condition",
]


# takes an initial info dict (t = 0), a pre info dict (t - 1), and elapsed time-steps,
# return if the condition is satisfied at the current step (t)
extra_spawn_condition_base = Callable[
    [
        Arg(dict, "ini_info_dict"),
        Arg(dict, "pre_info_dict"),
        Arg(int, "elapsed_timesteps"),
    ],
    bool,
]


def always_satisfy_condition(
    ini_info_dict: dict, pre_info_dict: dict, elapsed_timesteps: int
) -> bool:
    return True


def _check_below_height_condition(
    height_threshold: Union[float, int],
    ini_info_dict: dict,
    pre_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    Satisfy condition iff info["ypos"] <= height_threshold.
    Note that in MC, y-axis is the vertical axis.
    This is useful for extra diamond ore spawn (below y = 14)
    """
    return pre_info_dict["ypos"] <= height_threshold


def check_below_height_condition(
    height_threshold: Union[float, int]
) -> extra_spawn_condition_base:
    return partial(_check_below_height_condition, height_threshold=height_threshold)


def _check_above_height_condition(
    height_threshold: Union[float, int],
    ini_info_dict: dict,
    pre_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    Satisfy condition iff info["ypos"] >= height_threshold.
    Note that in MC, y-axis is the vertical axis.
    This is useful for extra plants spawn (above sea level y >= 62)
    """
    return pre_info_dict["ypos"] >= height_threshold


def check_above_height_condition(
    height_threshold: Union[float, int]
) -> extra_spawn_condition_base:
    return partial(_check_above_height_condition, height_threshold=height_threshold)


def _check_below_light_level_condition(
    light_level_threshold: Union[float, int],
    ini_info_dict: dict,
    pre_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    Satisfy condition iff info["light_level"] <= light_level_threshold
    Userful for extra monsters spawn (only spawn in dark/night)
    """
    return pre_info_dict["light_level"] <= light_level_threshold


def check_below_light_level_condition(light_level_threshold: Union[float, int]):
    return partial(
        _check_below_light_level_condition, light_level_threshold=light_level_threshold
    )


def _check_above_light_level_condition(
    light_level_threshold: Union[float, int],
    ini_info_dict: dict,
    pre_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    Satisfy condition iff info["light_level"] >= light_level_threshold
    Userful for extra passive mobs spawn
    """
    return pre_info_dict["light_level"] >= light_level_threshold


def check_above_light_level_condition(light_level_threshold: Union[float, int]):
    return partial(
        _check_above_light_level_condition, light_level_threshold=light_level_threshold
    )
