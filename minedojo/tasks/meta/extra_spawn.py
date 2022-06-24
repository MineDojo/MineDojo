from .utils import (
    check_below_height_condition,
    check_above_height_condition,
    check_above_light_level_condition,
    check_below_light_level_condition,
)

# TODO (yunfan): complete these dicts
# this dict specifies target items and corresponding blocks to obtain,
# e.g., break diamond ore to obtain a diamond
Target2SpawnItem = {
    # ore
    "cobblestone": "stone",
    "diamond": "diamond_ore",
    "redstone": "redstone_ore",
    "coal": "coal_ore",
    # ore byproduct
    "iron_ingot": "iron_ore",
    "gold_ingot": "gold_ore",
    # mob byproduct
    "leather": "cow",
    "mutton": "sheep",
    "porkchop": "pig",
    "beef": "cow",
    "bone": "skeleton",
    "web": "spider",
    "feather": "chicken",
    "wool": "sheep",
    "milk_bucket": "cow",
    # plant byproduct
    "wheat_seeds": "wheat",
    "beetroot_seeds": "beetroot",
    "pumpkin_seeds": "pumpkin",
}

# this dict specifies spawn conditions
SpawnItem2Condition = {
    # ore
    "stone": check_below_height_condition(height_threshold=60),
    "coal_ore": check_below_height_condition(height_threshold=60),
    "iron_ore": check_below_height_condition(height_threshold=50),
    "gold_ore": check_below_height_condition(height_threshold=29),
    "diamond_ore": check_below_height_condition(height_threshold=14),
    "redstone_ore": check_below_height_condition(height_threshold=16),
    # natural items
    "pumpkin": check_above_height_condition(height_threshold=62),
    "reeds": check_above_height_condition(height_threshold=62),
    "wheat": check_above_height_condition(height_threshold=62),
    "beetroot": check_above_height_condition(height_threshold=62),
    "potato": check_above_height_condition(height_threshold=62),
    "carrot": check_above_height_condition(height_threshold=62),
    # night mobs
    "zombie": check_below_light_level_condition(light_level_threshold=7),
    "creeper": check_below_light_level_condition(light_level_threshold=7),
    "spider": check_below_light_level_condition(light_level_threshold=7),
    "skeleton": check_below_light_level_condition(light_level_threshold=7),
    "witch": check_below_light_level_condition(light_level_threshold=7),
    "enderman": check_below_light_level_condition(light_level_threshold=7),
    "bat": check_below_light_level_condition(light_level_threshold=7),
    "husk": check_below_light_level_condition(light_level_threshold=7),
    "slime": check_below_light_level_condition(light_level_threshold=7),
    # day mobs
    "pig": check_above_light_level_condition(light_level_threshold=9),
    "cow": check_above_light_level_condition(light_level_threshold=9),
    "chicken": check_above_light_level_condition(light_level_threshold=9),
    "sheep": check_above_light_level_condition(light_level_threshold=9),
    "rabbit": check_above_light_level_condition(light_level_threshold=9),
    "horse": check_above_light_level_condition(light_level_threshold=9),
    "donkey": check_above_light_level_condition(light_level_threshold=9),
    "mooshroom": check_above_light_level_condition(light_level_threshold=9),
    "llama": check_above_light_level_condition(light_level_threshold=7),
}
