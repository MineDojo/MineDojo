from __future__ import annotations
import re
import sys
import importlib_resources
from itertools import product
from omegaconf import OmegaConf

from .meta.base import MetaTaskBase
from ..sim import MineDojoSim, InventoryItem
from ..sim.wrappers import FastResetWrapper, ARNNWrapper
from .meta import (
    HarvestMeta,
    CombatMeta,
    TechTreeMeta,
    Playthrough,
    SurvivalMeta,
    CreativeMeta,
)
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_stream_handler = logging.StreamHandler(stream=sys.stderr)
_stream_handler.setFormatter(logging.Formatter("[%(levelname)s:%(name)s] %(message)s"))
_logger.addHandler(_stream_handler)


def _resource_file_path(fname) -> str:
    with importlib_resources.as_file(
        importlib_resources.files("minedojo.tasks.description_files") / fname) as p:
        return str(p)


_MetaTaskName2Class = {
    "Open-Ended": MineDojoSim,
    "Harvest": HarvestMeta,
    "Combat": CombatMeta,
    "TechTree": TechTreeMeta,
    "Playthrough": Playthrough,
    "Survival": SurvivalMeta,
    "Creative": CreativeMeta,
}
MetaTaskName2Class = {k.lower(): v for k, v in _MetaTaskName2Class.items()}


def _meta_task_make(meta_task: str, *args, **kwargs) -> MetaTaskBase | FastResetWrapper:
    """
    Gym-style making tasks from names.

    Usage example:

    .. highlight:: python
    .. code-block:: python

        import minedojo
        env = minedojo.make(task_name, *args, **kwargs)

    Args:
        meta_task: Name of the meta task. Can be one of (and their lower-cased equivalents)
            ``"Open-Ended"``, ``"Harvest"``, ``"Combat"``, ``"TechTree"``,
            ``"Playthrough"``, ``"Survival"``, ``"Creative"``.

        *args: See corresponding task's docstring for more info.

        **kwargs: See corresponding task's docstring for more info.
    """
    meta_task = meta_task.lower()
    assert (
        meta_task in MetaTaskName2Class
    ), f"Invalid meta task name provided {meta_task}"
    if meta_task == "open-ended":
        if "fast_reset" in kwargs:
            fast_reset = kwargs.pop("fast_reset")
            fast_reset_random_teleport_range = kwargs.pop(
                "fast_reset_random_teleport_range", None
            )
            if fast_reset is True:
                return FastResetWrapper(
                    MineDojoSim(*args, **kwargs), fast_reset_random_teleport_range
                )
    return MetaTaskName2Class[meta_task](*args, **kwargs)


_ALL_TASKS_SPECS_UNFILLED = OmegaConf.load(_resource_file_path("tasks_specs.yaml"))
# check no duplicates
assert len(set(_ALL_TASKS_SPECS_UNFILLED.keys())) == len(_ALL_TASKS_SPECS_UNFILLED)

# all possible variables used to fill specs
_ALL_VARS = {
    # Combat
    "combat_biomes": ["forest", "plains", "extreme_hills"],
    "regular_biomes_mob": [
        "cow",
        "pig",
        "sheep",
        "chicken",
    ],
    "regular_biomes_night_mob": [
        "zombie",
        "spider",
        "skeleton",
        "creeper",
        "witch",
        "enderman",
    ],
    "end_mob": ["shulker", "endermite", "enderman",],
    "nether_mob": [
        "blaze",
        "ghast",
        "wither_skeleton",
        "zombie_pigman",
    ],
    "plains_mob": ["horse", "donkey"],
    "weapon_material": ["wooden", "iron", "diamond"],
    "armor_material": ["leather", "iron", "diamond"],
    # Harvest
    "quantity": [1, 8],
    ## wool and milk
    "cow_biomes": ["plains", "extreme_hills", "forest"],
    "sheep_biomes": ["plains", "extreme_hills", "forest"],
    ## mine
    "ore_type": ["iron_ore", "gold_ore", "diamond", "redstone", "coal", "cobblestone"],
    "pickaxe_material": ["wooden", "stone", "iron", "golden", "diamond"],
    ## most supported items (default only)
    "natural_items": [
        "nether_star",
        "blaze_rod",
        "ghast_tear",
        "nether_wart",
        "netherrack",
        "soul_sand",
        "chorus_flower",
        "chorus_fruit",
        "chorus_plant",
        "elytra",
        "end_stone",
        "ender_pearl",
        "apple",
        "beef",
        "beetroot",
        "beetroot_seeds",
        "bone",
        "brown_mushroom",
        "cactus",
        "carrot",
        "chicken",
        "dirt",
        "egg",
        "feather",
        "fish",
        "grass",
        "leaves",
        "log",
        "monster_egg",
        "mutton",
        "porkchop",
        "potato",
        "prismarine_shard",
        "pumpkin",
        "rabbit",
        "red_mushroom",
        "reeds",
        "sapling",
        "skull",
        "snowball",
        "spawn_egg",
        "sponge",
        "string",
        "totem_of_undying",
        "vine",
        "web",
        "wheat_seeds",
        "wheat",
    ],
    "craft_items": [
        "book",
        "carrot_on_a_stick",
        "clay",
        "crafting_table",
        "dye",
        "end_bricks",
        "end_rod",
        "ender_eye",
        "flint_and_steel",
        "glowstone",
        "gold_nugget",
        "iron_nugget",
        "iron_trapdoor",
        "lever",
        "nether_brick",
        "planks",
        "pumpkin_seeds",
        "red_nether_brick",
        "sandstone",
        "shears",
        "slime_ball",
        "stick",
        "stone_button",
        "stonebrick",
        "sugar",
        "torch",
        "trapped_chest",
        "wooden_button",
        "wool",
        "stone_pressure_plate",
    ],
    "crafting_table_items": [
        "anvil",
        "arrow",
        "banner",
        "beacon",
        "bed",
        "beetroot_soup",
        "boat",
        "bookshelf",
        "bowl",
        "bread",
        "bucket",
        "cake",
        "cauldron",
        "chest",
        "cookie",
        "end_crystal",
        "ender_chest",
        "fence",
        "fence_gate",
        "fire_charge",
        "fishing_rod",
        "flower_pot",
        "furnace",
        "glass_bottle",
        "glass_pane",
        "golden_apple",
        "hopper",
        "iron_bars",
        "ladder",
        "lead",
        "map",
        "minecart",
        "mushroom_stew",
        "painting",
        "paper",
        "pumpkin_pie",
        "rabbit_stew",
        "rail",
        "sea_lantern",
        "shield",
        "sign",
        "speckled_melon",
        "stone_slab",
        "trapdoor",
        "tripwire_hook",
        "wooden_door",
        "writable_book",
    ],
    "furnace_items": [
        "baked_potato",
        "brick",
        "cooked_beef",
        "cooked_chicken",
        "cooked_fish",
        "cooked_mutton",
        "cooked_porkchop",
        "cooked_rabbit",
        "glass",
        "gold_ingot",
        "iron_ingot",
        "quartz",
        "stone",
        "emerald",
        "netherbrick",
    ],
    ## core items
    ### most of the items here need trees in the biomes
    "biome_subset": ["plains", "jungle", "taiga", "forest", "swampland"],
    "natural_core": [
        "apple",
        "beef",
        "bone",
        "chicken",
        "log",
        "reeds",
        "web",
        "wheat",
    ],
    "hand_craft_core": [
        "flint_and_steel",
        "crafting_table",
        "planks",
        "shears",
        "stick",
        "sugar",
        "torch",
    ],
    "crafting_table_core": [
        "arrow",
        "chest",
        "shield",
        "fishing_rod",
        "bucket",
        "furnace",
    ],
    "furnace_core": [
        "cooked_beef",
        "glass",
        "gold_ingot",
        "iron_ingot",
        "brick",
        "stone",
    ],
    # Tech-tree
    "from_barehand_tools": ["wooden", "stone"],
    "from_barehand_tools_armor": ["iron", "golden", "diamond"],
    "from_wood_tools": ["stone"],
    "from_wood_tools_armor": ["iron", "golden", "diamond"],
    "from_stone_tools_armor": [
        "iron",
        "golden",
        "diamond",
    ],
    "from_iron_tools_armor": [
        "golden",
        "diamond",
    ],
    "from_gold_tools_armor": [
        "diamond",
    ],
    "target_tools": [
        "sword",
        "pickaxe",
        "axe",
        "hoe",
        "shovel",
    ],
    "target_armor": [
        "boots",
        "chestplate",
        "helmet",
        "leggings",
    ],
    "target_tools_armor": [
        "sword",
        "pickaxe",
        "axe",
        "hoe",
        "shovel",
        "boots",
        "chestplate",
        "helmet",
        "leggings",
    ],
    "redstone_list": [
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


def product_dict(**kwargs):
    keys = kwargs.keys()
    vals = kwargs.values()
    for instance in product(*vals):
        yield dict(zip(keys, instance))


ALL_TASKS_SPECS = {}
for task_id, task_specs in _ALL_TASKS_SPECS_UNFILLED.items():
    unfilled_vars = re.findall(r"\{(.*?)\}", task_id)

    def _recursive_find_unfilled_vars(x):
        if OmegaConf.is_dict(x):
            return {k: _recursive_find_unfilled_vars(v) for k, v in x.items()}
        elif isinstance(x, str):
            unfilled_vars.extend(re.findall(r"\{(.*?)\}", x))
        return x

    _recursive_find_unfilled_vars(task_specs)

    # deduplicate unfilled vars
    unfilled_vars = list(set(unfilled_vars))
    if len(unfilled_vars) == 0:
        # no unfilled vars, just make the task
        ALL_TASKS_SPECS[task_id] = task_specs
    else:
        unfilled_vars_values = {var: _ALL_VARS[var] for var in unfilled_vars}
        for var_dict in product_dict(**unfilled_vars_values):
            filled_task_id = task_id.format(**var_dict)

            def _recursive_replace_var(x):
                if OmegaConf.is_dict(x):
                    return {k: _recursive_replace_var(v) for k, v in x.items()}
                elif isinstance(x, str):
                    return x.format(**var_dict)
                return x

            task_specs_filled = _recursive_replace_var(task_specs)

            for k, v in task_specs_filled.items():
                if k == "target_quantities":
                    task_specs_filled[k] = int(v)
            task_specs_filled["prompt"] = task_specs_filled["prompt"].replace("_", " ")
            task_specs_filled["prompt"] = task_specs_filled["prompt"].replace(" 1", "")

            ALL_TASKS_SPECS[filled_task_id] = task_specs_filled

# check no duplicates
assert len(set(ALL_TASKS_SPECS.keys())) == len(ALL_TASKS_SPECS)

# load prompts and guidance for programmatic tasks
P_TASKS_PROMPTS_GUIDANCE = OmegaConf.load(
    _resource_file_path("programmatic_tasks.yaml")
)
# check no duplicates
assert len(set(P_TASKS_PROMPTS_GUIDANCE.keys())) == len(P_TASKS_PROMPTS_GUIDANCE)

# load prompts and guidance for creative tasks
C_TASKS_PROMPTS_GUIDANCE = OmegaConf.load(_resource_file_path("creative_tasks.yaml"))
# check no duplicates
assert len(set(C_TASKS_PROMPTS_GUIDANCE.keys())) == len(C_TASKS_PROMPTS_GUIDANCE)

# load prompt and guidance for Playthrough task
PLAYTHROUGH_PROMPT_GUIDANCE = OmegaConf.load(
    _resource_file_path("playthrough_task.yaml")
)
# check only one playthrough task
assert len(PLAYTHROUGH_PROMPT_GUIDANCE.keys()) == 1

ALL_PROGRAMMATIC_TASK_IDS = list(P_TASKS_PROMPTS_GUIDANCE.keys())
ALL_PROGRAMMATIC_TASK_INSTRUCTIONS = {
    task_id: (
        P_TASKS_PROMPTS_GUIDANCE[task_id]["prompt"],
        P_TASKS_PROMPTS_GUIDANCE[task_id]["guidance"],
    )
    for task_id in ALL_PROGRAMMATIC_TASK_IDS
}
ALL_CREATIVE_TASK_IDS = list(C_TASKS_PROMPTS_GUIDANCE.keys())
ALL_CREATIVE_TASK_INSTRUCTIONS = {
    task_id: (
        C_TASKS_PROMPTS_GUIDANCE[task_id]["prompt"],
        C_TASKS_PROMPTS_GUIDANCE[task_id]["guidance"],
    )
    for task_id in ALL_CREATIVE_TASK_IDS
}
PLAYTHROUGH_TASK_ID = list(PLAYTHROUGH_PROMPT_GUIDANCE.keys())[0]
PLAYTHROUGH_TASK_INSTRUCTION = (
    PLAYTHROUGH_PROMPT_GUIDANCE[PLAYTHROUGH_TASK_ID]["prompt"],
    PLAYTHROUGH_PROMPT_GUIDANCE[PLAYTHROUGH_TASK_ID]["guidance"],
)
ALL_TASK_IDS = ALL_PROGRAMMATIC_TASK_IDS + ALL_CREATIVE_TASK_IDS + [PLAYTHROUGH_TASK_ID]
ALL_TASK_INSTRUCTIONS = {
    **ALL_PROGRAMMATIC_TASK_INSTRUCTIONS,
    **ALL_CREATIVE_TASK_INSTRUCTIONS,
    PLAYTHROUGH_TASK_ID: PLAYTHROUGH_TASK_INSTRUCTION,
}

_logger.info(
    f"Loaded {len(P_TASKS_PROMPTS_GUIDANCE)} Programmatic tasks, "
    f"{len(C_TASKS_PROMPTS_GUIDANCE)} Creative tasks, "
    """and 1 special task: "Playthrough". """
    f"Totally {len(P_TASKS_PROMPTS_GUIDANCE) + len(C_TASKS_PROMPTS_GUIDANCE) + 1} tasks loaded."
)


def _parse_inventory_dict(inv_dict: dict[str, dict]) -> list[InventoryItem]:
    return [InventoryItem(slot=k, **v) for k, v in inv_dict.items()]


def _specific_task_make(task_id: str, *args, **kwargs):
    assert task_id in ALL_TASKS_SPECS, f"Invalid task id provided {task_id}"
    task_specs = ALL_TASKS_SPECS[task_id].copy()

    # handle list of inventory items
    if "initial_inventory" in task_specs:
        kwargs["initial_inventory"] = _parse_inventory_dict(
            task_specs["initial_inventory"]
        )
        task_specs.pop("initial_inventory")

    # pop prompt from task specs because it is set from programmatic yaml
    task_specs.pop("prompt")

    # meta task
    meta_task_cls = task_specs.pop("__cls__")
    task_obj = _meta_task_make(meta_task_cls, *args, **task_specs, **kwargs)
    return task_obj


def make(task_id: str, *args, cam_interval: int | float = 15, **kwargs):
    """
    Make a task. task_id can be one of the following:
    1. a task id for Programmatic tasks, e.g., "combat_bat_extreme_hills_barehand"
    2. format "creative:{idx}" for the idx-th Creative task
    3. "playthrough" or "open-ended" for these two special tasks
    4. one of "harvest", "combat", "techtree", and "survival" to creative meta task
    """
    if task_id.startswith("creative:"):
        creative_idx = int(task_id.split(":")[1])
        assert len(C_TASKS_PROMPTS_GUIDANCE) > creative_idx >= 0
        info = C_TASKS_PROMPTS_GUIDANCE[task_id]
        env_obj = _meta_task_make("creative", *args, **kwargs)
        env_obj.specify_prompt(info["prompt"])
        env_obj.specify_guidance(info["guidance"])
        env_obj.collection = info["collection"]
        env_obj.source = info["source"]
    elif task_id in P_TASKS_PROMPTS_GUIDANCE:
        info = P_TASKS_PROMPTS_GUIDANCE[task_id]
        env_obj = _specific_task_make(task_id, *args, **kwargs)
        env_obj.specify_prompt(info["prompt"])
        env_obj.specify_guidance(info["guidance"])
    elif task_id.lower() == PLAYTHROUGH_TASK_ID.lower():
        info = PLAYTHROUGH_PROMPT_GUIDANCE[PLAYTHROUGH_TASK_ID]
        env_obj = _specific_task_make(task_id, *args, **kwargs)
        env_obj.specify_prompt(info["prompt"])
        env_obj.specify_guidance(info["guidance"])
    elif task_id.lower() in [
        "open-ended",
        "harvest",
        "combat",
        "techtree",
        "survival",
    ]:
        env_obj = _meta_task_make(task_id, *args, **kwargs)
    else:
        raise ValueError(f"Invalid task id provided {task_id}")
    return ARNNWrapper(env_obj, cam_interval=cam_interval)
