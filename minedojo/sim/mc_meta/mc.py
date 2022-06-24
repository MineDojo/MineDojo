# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import os
import json

MC_ITEM_IDS = [
    "minecraft:acacia_boat",
    "minecraft:acacia_door",
    "minecraft:acacia_fence",
    "minecraft:acacia_fence_gate",
    "minecraft:acacia_stairs",
    "minecraft:activator_rail",
    "minecraft:air",
    "minecraft:anvil",
    "minecraft:apple",
    "minecraft:armor_stand",
    "minecraft:arrow",
    "minecraft:baked_potato",
    "minecraft:banner",
    "minecraft:barrier",
    "minecraft:beacon",
    "minecraft:bed",
    "minecraft:bedrock",
    "minecraft:beef",
    "minecraft:beetroot",
    "minecraft:beetroot_seeds",
    "minecraft:beetroot_soup",
    "minecraft:birch_boat",
    "minecraft:birch_door",
    "minecraft:birch_fence",
    "minecraft:birch_fence_gate",
    "minecraft:birch_stairs",
    "minecraft:black_glazed_terracotta",
    "minecraft:black_shulker_box",
    "minecraft:blaze_powder",
    "minecraft:blaze_rod",
    "minecraft:blue_glazed_terracotta",
    "minecraft:blue_shulker_box",
    "minecraft:boat",
    "minecraft:bone",
    "minecraft:bone_block",
    "minecraft:book",
    "minecraft:bookshelf",
    "minecraft:bow",
    "minecraft:bowl",
    "minecraft:bread",
    "minecraft:brewing_stand",
    "minecraft:brick",
    "minecraft:brick_block",
    "minecraft:brick_stairs",
    "minecraft:brown_glazed_terracotta",
    "minecraft:brown_mushroom",
    "minecraft:brown_mushroom_block",
    "minecraft:brown_shulker_box",
    "minecraft:bucket",
    "minecraft:cactus",
    "minecraft:cake",
    "minecraft:carpet",
    "minecraft:carrot",
    "minecraft:carrot_on_a_stick",
    "minecraft:cauldron",
    "minecraft:chain_command_block",
    "minecraft:chainmail_boots",
    "minecraft:chainmail_chestplate",
    "minecraft:chainmail_helmet",
    "minecraft:chainmail_leggings",
    "minecraft:chest",
    "minecraft:chest_minecart",
    "minecraft:chicken",
    "minecraft:chorus_flower",
    "minecraft:chorus_fruit",
    "minecraft:chorus_fruit_popped",
    "minecraft:chorus_plant",
    "minecraft:clay",
    "minecraft:clay_ball",
    "minecraft:clock",
    "minecraft:coal",
    "minecraft:coal_block",
    "minecraft:coal_ore",
    "minecraft:cobblestone",
    "minecraft:cobblestone_wall",
    "minecraft:command_block",
    "minecraft:command_block_minecart",
    "minecraft:comparator",
    "minecraft:compass",
    "minecraft:concrete",
    "minecraft:concrete_powder",
    "minecraft:cooked_beef",
    "minecraft:cooked_chicken",
    "minecraft:cooked_fish",
    "minecraft:cooked_mutton",
    "minecraft:cooked_porkchop",
    "minecraft:cooked_rabbit",
    "minecraft:cookie",
    "minecraft:crafting_table",
    "minecraft:cyan_glazed_terracotta",
    "minecraft:cyan_shulker_box",
    "minecraft:dark_oak_boat",
    "minecraft:dark_oak_door",
    "minecraft:dark_oak_fence",
    "minecraft:dark_oak_fence_gate",
    "minecraft:dark_oak_stairs",
    "minecraft:daylight_detector",
    "minecraft:deadbush",
    "minecraft:detector_rail",
    "minecraft:diamond",
    "minecraft:diamond_axe",
    "minecraft:diamond_block",
    "minecraft:diamond_boots",
    "minecraft:diamond_chestplate",
    "minecraft:diamond_helmet",
    "minecraft:diamond_hoe",
    "minecraft:diamond_horse_armor",
    "minecraft:diamond_leggings",
    "minecraft:diamond_ore",
    "minecraft:diamond_pickaxe",
    "minecraft:diamond_shovel",
    "minecraft:diamond_sword",
    "minecraft:dirt",
    "minecraft:dispenser",
    "minecraft:double_plant",
    "minecraft:dragon_breath",
    "minecraft:dragon_egg",
    "minecraft:dropper",
    "minecraft:dye",
    "minecraft:egg",
    "minecraft:elytra",
    "minecraft:emerald",
    "minecraft:emerald_block",
    "minecraft:emerald_ore",
    "minecraft:enchanted_book",
    "minecraft:enchanting_table",
    "minecraft:end_bricks",
    "minecraft:end_crystal",
    "minecraft:end_portal_frame",
    "minecraft:end_rod",
    "minecraft:end_stone",
    "minecraft:ender_chest",
    "minecraft:ender_eye",
    "minecraft:ender_pearl",
    "minecraft:experience_bottle",
    "minecraft:farmland",
    "minecraft:feather",
    "minecraft:fence",
    "minecraft:fence_gate",
    "minecraft:fermented_spider_eye",
    "minecraft:filled_map",
    "minecraft:fire_charge",
    "minecraft:firework_charge",
    "minecraft:fireworks",
    "minecraft:fish",
    "minecraft:fishing_rod",
    "minecraft:flint",
    "minecraft:flint_and_steel",
    "minecraft:flower_pot",
    "minecraft:furnace",
    "minecraft:furnace_minecart",
    "minecraft:ghast_tear",
    "minecraft:glass",
    "minecraft:glass_bottle",
    "minecraft:glass_pane",
    "minecraft:glowstone",
    "minecraft:glowstone_dust",
    "minecraft:gold_block",
    "minecraft:gold_ingot",
    "minecraft:gold_nugget",
    "minecraft:gold_ore",
    "minecraft:golden_apple",
    "minecraft:golden_axe",
    "minecraft:golden_boots",
    "minecraft:golden_carrot",
    "minecraft:golden_chestplate",
    "minecraft:golden_helmet",
    "minecraft:golden_hoe",
    "minecraft:golden_horse_armor",
    "minecraft:golden_leggings",
    "minecraft:golden_pickaxe",
    "minecraft:golden_rail",
    "minecraft:golden_shovel",
    "minecraft:golden_sword",
    "minecraft:grass",
    "minecraft:grass_path",
    "minecraft:gravel",
    "minecraft:gray_glazed_terracotta",
    "minecraft:gray_shulker_box",
    "minecraft:green_glazed_terracotta",
    "minecraft:green_shulker_box",
    "minecraft:gunpowder",
    "minecraft:hardened_clay",
    "minecraft:hay_block",
    "minecraft:heavy_weighted_pressure_plate",
    "minecraft:hopper",
    "minecraft:hopper_minecart",
    "minecraft:ice",
    "minecraft:iron_axe",
    "minecraft:iron_bars",
    "minecraft:iron_block",
    "minecraft:iron_boots",
    "minecraft:iron_chestplate",
    "minecraft:iron_door",
    "minecraft:iron_helmet",
    "minecraft:iron_hoe",
    "minecraft:iron_horse_armor",
    "minecraft:iron_ingot",
    "minecraft:iron_leggings",
    "minecraft:iron_nugget",
    "minecraft:iron_ore",
    "minecraft:iron_pickaxe",
    "minecraft:iron_shovel",
    "minecraft:iron_sword",
    "minecraft:iron_trapdoor",
    "minecraft:item_frame",
    "minecraft:jukebox",
    "minecraft:jungle_boat",
    "minecraft:jungle_door",
    "minecraft:jungle_fence",
    "minecraft:jungle_fence_gate",
    "minecraft:jungle_stairs",
    "minecraft:ladder",
    "minecraft:lapis_block",
    "minecraft:lapis_ore",
    "minecraft:lava_bucket",
    "minecraft:lead",
    "minecraft:leather",
    "minecraft:leather_boots",
    "minecraft:leather_chestplate",
    "minecraft:leather_helmet",
    "minecraft:leather_leggings",
    "minecraft:leaves",
    "minecraft:leaves2",
    "minecraft:lever",
    "minecraft:light_blue_glazed_terracotta",
    "minecraft:light_blue_shulker_box",
    "minecraft:light_weighted_pressure_plate",
    "minecraft:lime_glazed_terracotta",
    "minecraft:lime_shulker_box",
    "minecraft:lingering_potion",
    "minecraft:lit_pumpkin",
    "minecraft:log",
    "minecraft:log2",
    "minecraft:magenta_glazed_terracotta",
    "minecraft:magenta_shulker_box",
    "minecraft:magma",
    "minecraft:magma_cream",
    "minecraft:map",
    "minecraft:melon",
    "minecraft:melon_block",
    "minecraft:melon_seeds",
    "minecraft:milk_bucket",
    "minecraft:minecart",
    "minecraft:mob_spawner",
    "minecraft:monster_egg",
    "minecraft:mossy_cobblestone",
    "minecraft:mushroom_stew",
    "minecraft:mutton",
    "minecraft:mycelium",
    "minecraft:name_tag",
    "minecraft:nether_brick",
    "minecraft:nether_brick_fence",
    "minecraft:nether_brick_stairs",
    "minecraft:nether_star",
    "minecraft:nether_wart",
    "minecraft:nether_wart_block",
    "minecraft:netherbrick",
    "minecraft:netherrack",
    "minecraft:noteblock",
    "minecraft:oak_stairs",
    "minecraft:observer",
    "minecraft:obsidian",
    "minecraft:orange_glazed_terracotta",
    "minecraft:orange_shulker_box",
    "minecraft:packed_ice",
    "minecraft:painting",
    "minecraft:paper",
    "minecraft:pink_glazed_terracotta",
    "minecraft:pink_shulker_box",
    "minecraft:piston",
    "minecraft:planks",
    "minecraft:poisonous_potato",
    "minecraft:porkchop",
    "minecraft:potato",
    "minecraft:potion",
    "minecraft:prismarine",
    "minecraft:prismarine_crystals",
    "minecraft:prismarine_shard",
    "minecraft:pumpkin",
    "minecraft:pumpkin_pie",
    "minecraft:pumpkin_seeds",
    "minecraft:purple_glazed_terracotta",
    "minecraft:purple_shulker_box",
    "minecraft:purpur_block",
    "minecraft:purpur_pillar",
    "minecraft:purpur_slab",
    "minecraft:purpur_stairs",
    "minecraft:quartz",
    "minecraft:quartz_block",
    "minecraft:quartz_ore",
    "minecraft:quartz_stairs",
    "minecraft:rabbit",
    "minecraft:rabbit_foot",
    "minecraft:rabbit_hide",
    "minecraft:rabbit_stew",
    "minecraft:rail",
    "minecraft:record_11",
    "minecraft:record_13",
    "minecraft:record_blocks",
    "minecraft:record_cat",
    "minecraft:record_chirp",
    "minecraft:record_far",
    "minecraft:record_mall",
    "minecraft:record_mellohi",
    "minecraft:record_stal",
    "minecraft:record_strad",
    "minecraft:record_wait",
    "minecraft:record_ward",
    "minecraft:red_flower",
    "minecraft:red_glazed_terracotta",
    "minecraft:red_mushroom",
    "minecraft:red_mushroom_block",
    "minecraft:red_nether_brick",
    "minecraft:red_sandstone",
    "minecraft:red_sandstone_stairs",
    "minecraft:red_shulker_box",
    "minecraft:redstone",
    "minecraft:redstone_block",
    "minecraft:redstone_lamp",
    "minecraft:redstone_ore",
    "minecraft:redstone_torch",
    "minecraft:reeds",
    "minecraft:repeater",
    "minecraft:repeating_command_block",
    "minecraft:rotten_flesh",
    "minecraft:saddle",
    "minecraft:sand",
    "minecraft:sandstone",
    "minecraft:sandstone_stairs",
    "minecraft:sapling",
    "minecraft:sea_lantern",
    "minecraft:shears",
    "minecraft:shield",
    "minecraft:shulker_shell",
    "minecraft:sign",
    "minecraft:silver_glazed_terracotta",
    "minecraft:silver_shulker_box",
    "minecraft:skull",
    "minecraft:slime",
    "minecraft:slime_ball",
    "minecraft:snow",
    "minecraft:snow_layer",
    "minecraft:snowball",
    "minecraft:soul_sand",
    "minecraft:spawn_egg",
    "minecraft:speckled_melon",
    "minecraft:spectral_arrow",
    "minecraft:spider_eye",
    "minecraft:splash_potion",
    "minecraft:sponge",
    "minecraft:spruce_boat",
    "minecraft:spruce_door",
    "minecraft:spruce_fence",
    "minecraft:spruce_fence_gate",
    "minecraft:spruce_stairs",
    "minecraft:stained_glass",
    "minecraft:stained_glass_pane",
    "minecraft:stained_hardened_clay",
    "minecraft:stick",
    "minecraft:sticky_piston",
    "minecraft:stone",
    "minecraft:stone_axe",
    "minecraft:stone_brick_stairs",
    "minecraft:stone_button",
    "minecraft:stone_hoe",
    "minecraft:stone_pickaxe",
    "minecraft:stone_pressure_plate",
    "minecraft:stone_shovel",
    "minecraft:stone_slab",
    "minecraft:stone_slab2",
    "minecraft:stone_stairs",
    "minecraft:stone_sword",
    "minecraft:stonebrick",
    "minecraft:string",
    "minecraft:structure_block",
    "minecraft:structure_void",
    "minecraft:sugar",
    "minecraft:tallgrass",
    "minecraft:tipped_arrow",
    "minecraft:tnt",
    "minecraft:tnt_minecart",
    "minecraft:torch",
    "minecraft:totem_of_undying",
    "minecraft:trapdoor",
    "minecraft:trapped_chest",
    "minecraft:tripwire_hook",
    "minecraft:vine",
    "minecraft:water_bucket",
    "minecraft:waterlily",
    "minecraft:web",
    "minecraft:wheat",
    "minecraft:wheat_seeds",
    "minecraft:white_glazed_terracotta",
    "minecraft:white_shulker_box",
    "minecraft:wooden_axe",
    "minecraft:wooden_button",
    "minecraft:wooden_door",
    "minecraft:wooden_hoe",
    "minecraft:wooden_pickaxe",
    "minecraft:wooden_pressure_plate",
    "minecraft:wooden_shovel",
    "minecraft:wooden_slab",
    "minecraft:wooden_sword",
    "minecraft:wool",
    "minecraft:writable_book",
    "minecraft:written_book",
    "minecraft:yellow_flower",
    "minecraft:yellow_glazed_terracotta",
    "minecraft:yellow_shulker_box",
]

ALL_ACHIEVEMENTS = [
    "achievement.openInventory",
    "achievement.mineWood",
    "achievement.buildWorkBench",
    "achievement.buildPickaxe",
    "achievement.buildFurnace",
    "achievement.acquireIron",
    "achievement.buildHoe",
    "achievement.makeBread",
    "achievement.bakeCake",
    "achievement.buildBetterPickaxe",
    "achievement.cookFish",
    "achievement.onARail",
    "achievement.buildSword",
    "achievement.killEnemy",
    "achievement.killCow",
    "achievement.flyPig",
    "achievement.snipeSkeleton",
    "achievement.diamonds",
    "achievement.diamondsToYou",
    "achievement.portal",
    "achievement.ghast",
    "achievement.blazeRod",
    "achievement.potion",
    "achievement.theEnd",
    "achievement.theEnd2",
    "achievement.enchantments",
    "achievement.overkill",
    "achievement.bookcase",
    "achievement.breedCow",
    "achievement.spawnWither",
    "achievement.killWither",
    "achievement.fullBeacon",
    "achievement.exploreAllBiomes",
    "achievement.overpowered",
]

KEYMAP = {
    "17": "forward",
    "30": "left",
    "31": "back",
    "32": "right",
    "57": "jump",
    "18": "inventory",
    "16": "drop",
    "42": "sneak",
    "29": "sprint",
    "-100": "attack",  # BUTTON0 Left Click
    "-99": "use",  # BUTTON1 Right Click
    "-98": "pickItem",  # BUTTON2 Middle Click
    # '20': 'chat',  # This and following not currently in use
    # '33': 'swapHands',
    # '15': 'playerlist',  # Show player list gui
    # '53': 'command',  # Start typing server cmd
    # '60': 'screenshot',
    # '63': 'togglePerspective',
    # '87': 'fullscreen',
    # '46': 'saveToolbarActivator',
    # '45': 'loadToolbarActivator',
    # '38': 'advancements',
}

KEYMAP.update({str(x + 1): str(x) for x in range(1, 10)})

# TODO: add all other keys.
INVERSE_KEYMAP = {KEYMAP[key]: key for key in KEYMAP}

MAX_LIFE = 20  # Actual max life can be greater (e.g. after eating a golden apple)
MAX_ARMOR = 20  # actual max armor value (i.e., wearing a full suit of diamond armors)
MAX_XP = 1395  # Represents level 30 in game - bounded by signed 32 bit int max
MAX_BREATH = 300  # Should be max encountered - subject to change by mods
MAX_FOOD = 20  # Default max food
MAX_FOOD_SATURATION = 20.0  # Current max saturation limit as of 1.11.2
MAX_SCORE = 0x7FFFFF  # Implemented as XP in survival but can change e.g. mini-games


def get_item_id(item: str) -> int:
    """
    Gets the item ID of an MC item.
    :param item: The item string
    :return: The internal ID of the item.
    """
    if not item.startswith("minecraft:"):
        item = "minecraft:" + item

    return MC_ITEM_IDS.index(item)


def get_key_from_id(id: str) -> str:
    """
    Gets the key from an id.
    :param id:
    :return:
    """
    assert id in KEYMAP, "ID not found"
    return KEYMAP[id]


mc_constants_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "mc_constants.json"
)
all_data = json.load(open(mc_constants_file))

ALL_ITEMS = sorted([item["type"] for item in all_data["items"]])
ALL_ITEM_VARIANTS = sorted(
    [
        f"{item['type']}_{variant}"
        for item in all_data["items"]
        if "variant" in item
        for variant in item["variant"]
    ]
)

ALL_STATS = sorted([stat["statID"] for stat in all_data["stats"]])
ALL_STAT_KEYS = sorted([stat["minerl_keys"] for stat in all_data["stats"]])

# We choose these not to be included by default; they are not items.
NONE = "none"
INVALID = "invalid"

# TODO remove hack based on ordering in MineRL
MINERL_ITEM_MAP = sorted(["none"] + ALL_ITEMS)

ITEMS_BY_CATEGORY = {
    # Items which take 2 seconds to USE
    "edible": [
        item["type"]
        for item in all_data["items"]
        if item["useAction"] in {"EAT", "DRINK"}
    ],
    # Items which have ongoing effect when equipped (includes armor)
    "tool": [
        item["type"] for item in all_data["items"] if item["tab"] in {"tools", "combat"}
    ],
    # Items which are used for building
    "building_block": [
        item["type"] for item in all_data["items"] if item["tab"] in {"buildingBlock"}
    ],
    # Redstone items (doors, buttons, levers)
    "redstone": [
        item["type"] for item in all_data["items"] if item["tab"] in {"redstone"}
    ],
    # Brewing items
    "brewing": [
        item["type"] for item in all_data["items"] if item["tab"] in {"brewing"}
    ],
    # Decoration items (includes torch)
    "decoration": [
        item["type"] for item in all_data["items"] if item["tab"] in {"decoration"}
    ],
}


PLACEABLE_ITEM_NAMES = sorted(
    [
        item["type"].replace("_", " ")
        for item in all_data["items"]
        if item["block"] is True
    ]
)


# Check that all edible items have the same maxUseDuration
use_times = {
    item["maxUseDuration"]
    for item in all_data["items"]
    if item["useAction"] in {"EAT", "DRINK"}
}
assert len(use_times) == 1, "Edible items with multiple different eating times."
EDIBLE_USE_TICKS = use_times.pop()


def recursive_dict_eq(d1, d2):
    if isinstance(d1, dict) != isinstance(d2, dict):
        return False
    if isinstance(d1, dict):
        if set(d1.keys()) != set(d2.keys()):
            return False
        return all([recursive_dict_eq(d1[k], d2[k]) for k in d1.keys()])
    else:
        return d1 == d2


def duplicate_dict_in_list(dict, list):
    for item in list:
        if recursive_dict_eq(dict, item):
            return True
    return False


def dedup_list(dicts):
    """
    Takes a list of dictionary objects and removes any duplicates (compared recursively by value).
    """
    result = []
    for next_dict in dicts:
        if not duplicate_dict_in_list(next_dict, result):
            result.append(next_dict)
    return result


def sort_recipes_by_output(json):
    result = {item: [] for item in ALL_ITEMS}
    for recipe in json:
        if len(recipe["ingredients"]) == 0:
            # Empty recipe
            continue
        if recipe["outputItemName"] in recipe["ingredients"]:
            # Circular recipe
            continue
        result[recipe["outputItemName"]].append(recipe)
    for item, recipes in result.items():
        result[item] = dedup_list(recipes)
    return result


CRAFTING_RECIPES_BY_OUTPUT = sort_recipes_by_output(all_data["craftingRecipes"])
SMELTING_RECIPES_BY_OUTPUT = sort_recipes_by_output(all_data["smeltingRecipes"])

ALL_PERSONAL_CRAFTING_ITEMS = sorted(
    [
        item["type"]
        for item in all_data["items"]
        if item["type"] in CRAFTING_RECIPES_BY_OUTPUT.keys()
        and len(CRAFTING_RECIPES_BY_OUTPUT[item["type"]]) > 0
        and all(
            [
                recipe["recipeSize"] in [0, 1, 2, 4]  # TODO recipeSize needs to be 2D
                for recipe in CRAFTING_RECIPES_BY_OUTPUT[item["type"]]
            ]
        )
    ]
)

ALL_CRAFTING_TABLE_ITEMS = sorted(
    [
        item["type"]
        for item in all_data["items"]
        if item["type"] in CRAFTING_RECIPES_BY_OUTPUT.keys()
        and len(CRAFTING_RECIPES_BY_OUTPUT[item["type"]]) > 0
        and any(
            [
                recipe["recipeSize"] <= 9
                for recipe in CRAFTING_RECIPES_BY_OUTPUT[item["type"]]
            ]
        )
    ]
)

ALL_CRAFTING_TABLE_ONLY_ITEMS = sorted(
    [x for x in ALL_CRAFTING_TABLE_ITEMS if x not in ALL_PERSONAL_CRAFTING_ITEMS]
)

ALL_SMELTING_ITEMS = sorted(
    [
        item["type"]
        for item in all_data["items"]
        if item["type"] in SMELTING_RECIPES_BY_OUTPUT.keys()
        and len(SMELTING_RECIPES_BY_OUTPUT[item["type"]]) > 0
    ]
)

# all self-craftable/table craftable/smeltable items, including "none"
ALL_HAND_CRAFT_ITEMS_NN_ACTIONS = [
    x
    for x in ALL_PERSONAL_CRAFTING_ITEMS
    if x
    not in [
        "coal",
        "diamond",
        "emerald",
        "gold_ingot",
        "iron_ingot",
        "redstone",
        "stone",
    ]
]
ALL_TABLE_CRAFT_ONLY_ITEMS_NN_ACTIONS = [
    x for x in ALL_CRAFTING_TABLE_ONLY_ITEMS if x not in ["iron_ingot", "gold_ingot"]
]
ALL_SMELT_ITEMS_NN_ACTIONS = [
    x for x in ALL_SMELTING_ITEMS if x not in ["iron_nugget", "dye", "gold_nugget"]
]
ALL_CRAFT_SMELT_ITEMS = (
    ALL_HAND_CRAFT_ITEMS_NN_ACTIONS
    + ALL_TABLE_CRAFT_ONLY_ITEMS_NN_ACTIONS
    + ALL_SMELT_ITEMS_NN_ACTIONS
)

assert len(set(ALL_CRAFT_SMELT_ITEMS)) == len(ALL_HAND_CRAFT_ITEMS_NN_ACTIONS) + len(
    ALL_TABLE_CRAFT_ONLY_ITEMS_NN_ACTIONS
) + len(ALL_SMELT_ITEMS_NN_ACTIONS)

EQUIPMENT_SLOTS = [
    "mainhand",
    "offhand",
    "feet",
    "legs",
    "chest",
    "head",
]

BEST_ITEMS_PER_EQUIPMENT_SLOT = {
    equip: [
        item["type"] for item in all_data["items"] if item["bestEquipmentSlot"] == equip
    ]
    for equip in EQUIPMENT_SLOTS
}

NON_MAINHAND_ITEM_NAMES = []
for k, v in BEST_ITEMS_PER_EQUIPMENT_SLOT.items():
    if k != "mainhand":
        NON_MAINHAND_ITEM_NAMES.extend([item.replace("_", " ") for item in v])

N_INV_SLOTS = 36  # including main-hand

MS_PER_STEP = 50
STEPS_PER_MS = 1 / 50


def strip_item_prefix(minecraft_name):
    # Names in minecraft start with 'minecraft:', like:
    # 'minecraft:log', or 'minecraft:cobblestone'
    if minecraft_name.startswith("minecraft:"):
        return minecraft_name[len("minecraft:") :]

    return minecraft_name


# Transcribed from: https://minecraft.gamepedia.com/index.php?title=Biome&oldid=1057817,
#   which has the biomes as they were during the minecraft version at the time: 1.11.2
# _m indicates that the terrain is more mountainous
# _f indicates that the terrain has trees where the base biome does not.
BIOMES_MAP = {
    "ice_plains": 12,
    "ice_plains_spikes": 140,
    "cold_taiga": 30,
    "cold_taiga_m": 158,
    "frozen_river": 11,
    "cold_beach": 26,
    "extreme_hills": 3,
    "extreme_hills_m": 131,
    "extreme_hills_plus": 34,
    "extreme_hills_plus_m": 162,
    "taiga": 5,
    "taiga_m": 133,
    "mega_taiga": 32,
    "mega_spruce_taiga": 160,
    "stone_beach": 25,
    "plains": 1,
    "sunflower_plains": 129,
    "forest": 4,
    "flower_forest": 132,
    "birch_forest": 27,
    "birch_forest_m": 155,
    "roofed_forest": 29,
    "roofed_forest_m": 157,
    "swampland": 6,
    "swampland_m": 134,
    "jungle": 21,
    "jungle_m": 149,
    "jungle_edge": 23,
    "jungle_edge_m": 151,
    "river": 7,
    "beach": 16,
    "mushroom_island": 14,
    "mushroom_island_shore": 15,
    "desert": 2,
    "desert_m": 130,
    "savanna": 35,
    "savanna_m": 163,
    "mesa": 37,
    "mesa_bryce": 165,
    "mesa_plateau_f": 38,
    "mesa_plateau_f_m": 166,
    "savanna_plateau": 36,
    "mesa_plateau": 39,
    "savanna_plateau_m": 164,
    "mesa_plateau_m": 167,
    "ocean": 0,
    "deep_ocean": 24,
    "ice_mountains": 13,
    "desert_hills": 17,
    "forest_hills": 18,
    "taiga_hills": 19,
    "jungle_hills": 22,
    "birch_forest_hills": 28,
    "cold_taiga_hills": 31,
    "mega_taiga_hills": 33,
    "tall_birch_hills": 156,
    "mega_spruce_taiga_hills": 161,
    "plains_m": 128,
    "frozen_ocean": 10,
    "extreme_hills_edge": 20,
    "the_end": 9,
    "nether": 8,
    "the_void": 127,
}
