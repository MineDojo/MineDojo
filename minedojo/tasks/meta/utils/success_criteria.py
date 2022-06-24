from functools import partial
from mypy_extensions import Arg
from typing import Callable, List, Dict, Union


__all__ = [
    "check_success_base",
    "simple_inventory_based_check",
    "simple_stat_kill_entity_based_check",
    "time_since_death_check",
    "use_any_item_check",
    "use_all_item_check",
]


# takes an initial info dict, a current info dict, and elapsed time-steps, return successful or not
check_success_base = Callable[
    [
        Arg(dict, "ini_info_dict"),
        Arg(dict, "cur_info_dict"),
        Arg(int, "elapsed_timesteps"),
    ],
    bool,
]


def _simple_stat_kill_entity_based_check(
    name: str,
    quantity: int,
    ini_info_dict: dict,
    cur_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    A simple success check based on `info["stat"]["kill_entity"][{name}]`.
    """
    return (
        cur_info_dict["stat"]["kill_entity"][name]
        - ini_info_dict["stat"]["kill_entity"][name]
    ) >= quantity


def simple_stat_kill_entity_based_check(
    name: str, quantity: int, **kwargs
) -> check_success_base:
    return partial(_simple_stat_kill_entity_based_check, name=name, quantity=quantity)


def _simple_inventory_based_check(
    name: str,
    quantity: int,
    ini_info_dict: dict,
    cur_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    A simple success check based on `info["inventory"]`
    """
    return (
        sum(
            [
                inv_item["quantity"]
                for inv_item in cur_info_dict["inventory"]
                if inv_item["name"] == name
            ]
        )
        - sum(
            [
                inv_item["quantity"]
                for inv_item in ini_info_dict["inventory"]
                if inv_item["name"] == name
            ]
        )
    ) >= quantity


def simple_inventory_based_check(
    name: str, quantity: int, **kwargs
) -> check_success_base:
    return partial(_simple_inventory_based_check, name=name, quantity=quantity)


def _time_since_death_check(
    threshold, ini_info_dict: dict, cur_info_dict: dict, elapsed_timesteps: int
):
    """
    Success check based on info["time_since_death"]
    """
    return cur_info_dict["stat"]["time_since_death"] >= threshold


def time_since_death_check(threshold, **kwargs) -> check_success_base:
    return partial(_time_since_death_check, threshold=threshold)


def _use_any_item_check(
    targets: Dict[str, int],
    ini_info_dict: dict,
    cur_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    success check based on increment in info["stat"]["use_item"]["minecraft"][item]
    satisfaction of any item will result in "True" -- the logic "any"
    """
    return any(
        [
            (
                cur_info_dict["stat"]["use_item"]["minecraft"][item]
                - ini_info_dict["stat"]["use_item"]["minecraft"][item]
            )
            >= target
            for item, target in targets.items()
        ]
    )


def use_any_item_check(targets: Dict[str, int]) -> check_success_base:
    return partial(_use_any_item_check, targets=targets)


def _use_all_item_check(
    targets: Dict[str, int],
    ini_info_dict: dict,
    cur_info_dict: dict,
    elapsed_timesteps: int,
):
    """
    success check based on increment in info["stat"]["use_item"]["minecraft"][item]
    satisfaction of all item will result in "True" -- the logic "all"
    """
    return all(
        [
            (
                cur_info_dict["stat"]["use_item"]["minecraft"][item]
                - ini_info_dict["stat"]["use_item"]["minecraft"][item]
            )
            >= target
            for item, target in targets.items()
        ]
    )


def use_all_item_check(targets: Dict[str, int]) -> check_success_base:
    return partial(_use_all_item_check, targets=targets)
