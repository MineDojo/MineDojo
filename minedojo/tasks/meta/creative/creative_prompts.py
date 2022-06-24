materials = [
    "diamond",
    "gold",
    "iron",
    "stone",
    "glass",
    "sand",
]
architectures_farm = [
    "house",
    "castle",
    "temple",
    "pyramid",
    "tower",
]

architectures = [
    "ice house",
    "sand castle",
    "glass temple",
    "dirt pyramid",
    "wooden tower",
    "stone cathedral",
    "iron hospital",
    "gold school",
    "diamond skyscraper",
]
statues = [
    "diamond car",
    "glod train",
    "iron plane",
    "stone apple",
    "wooden dog",
    "glass cat",
    "ice man",
    "sand woman",
]

famous_sight = [
    "Grand Canyon",
    "Roman Colosseum",
    "Eiffel Tower",
    "Taj Mahal",
    "Notre Dame",
    "Great Wall",
    "Statue of Liberty",
    "Cologne Cathedral",
    "Sydney Opera House",
    "Acropolis",
    "Golden Gate Bridge",
    "Leaning Tower of Pisa",
]

natural_scenes = [
    "waterfall",
    "lava fall",
    "tree",
    "cave",
    "mountain",
    "lake",
    "lava lake",
]

view_point_2d = ["top-down", "vertical", "panorama", "half-panorama"]

passive_mobs = ["pig", "sheep", "cow", "chicken"]
hostile_mobs = ["zombie", "creeper", "skeleton", "spider"]

automatic_farms = [
    "wheat",
    "gold",
    "cow",
    "sheep",
    "sugar cane",
    "hostile mob",
    "wool",
]

explore_targets = [
    "plains",
    "forest",
    "ocean",
    "river",
    "beach",
    "taiga",
    "mountains",
    "ice spikes",
    "jungle",
    "desert",
    "swampland",
    "end city",
    "ocean monument",
    "desert temple",
    "woodland mansion",
    "cave",
    "mineshaft",
    "swamp hut",
    "jungle temple",
    "mushroom island",
    "nether",
    "village",
    "pyramid",
    "cliff",
    "waterfall",
    "lavafall",
    "lake",
    "lava lake",
    "underground lake",
]

all_task = {
    "explore": dict(
        template="Explore the world to find {explore_targets}.",
        parameters=dict(
            explore_targets=explore_targets,
        ),
    ),
    "architecture": dict(
        template="Build a {architectures}.",
        parameters=dict(
            architectures=architectures,
        ),
    ),
    "farm": dict(
        template="Build a {passive_mobs} farm.",
        parameters=dict(
            passive_mobs=passive_mobs,
        ),
    ),
    "farm_architectures": dict(
        template="Build a {passive_mobs} farm in {architectures_farm}.",
        parameters=dict(
            passive_mobs=passive_mobs,
            architectures_farm=architectures_farm,
        ),
    ),
    "natural_scenes": dict(
        template="Build an artificial {natural_scenes}.",
        parameters=dict(natural_scenes=natural_scenes),
    ),
    "statue": dict(
        template="Build a {statues} statue.",
        parameters=dict(statues=statues),
    ),
    "famous_sight": dict(
        template="Build the {famous_sight}.",
        parameters=dict(
            famous_sight=famous_sight,
        ),
    ),
    "automatic_farm": dict(
        template="Build an automatic {resource} farm.",
        parameters=dict(
            resource=automatic_farms,
        ),
    ),
    "haunted_house": dict(
        template="Build a Haunted House with {hostile_mobs} inside.",
        parameters=dict(
            hostile_mobs=hostile_mobs,
        ),
    ),
    "swimming_pool": dict(
        template="Build a swimming pool.",
        parameters=dict(),
    ),
    "maze": dict(
        template="Build a maze using {materials}.",
        parameters=dict(materials=materials),
    ),
    "archery_range": dict(
        template="Build an archery range.",
        parameters=dict(),
    ),
    "bridge": dict(
        template="Build a bridge over a {fluid}.",
        parameters=dict(
            fluid=["river", "lake", "lava"],
        ),
    ),
    "light_tree": dict(
        template="Build a tree that can be lighted up.",
        parameters=dict(),
    ),
    "trap": dict(
        template="Trap a {hostile_mobs} in {containers}.",
        parameters=dict(
            hostile_mobs=hostile_mobs,
            containers=architectures_farm + ["wooden cage", "stone cage"],
        ),
    ),
    "gather": dict(
        template="Gather nearby {passive_mobs} in a {architectures_farm}.",
        parameters=dict(
            passive_mobs=passive_mobs,
            architectures_farm=architectures_farm,
        ),
    ),
    "travel_long_distance": dict(
        template="Travel over {distance} blocks by {approach}.",
        parameters=dict(
            distance=[1000, 2000, 3000],
            approach=[
                "ice boat",
                "nether portals",
                "mine cart",
                "riding horse",
                "riding pig",
            ],
        ),
    ),
    "fill_map": dict(
        template="Fill a map of the world.",
        parameters=dict(),
    ),
    "reach_upperbound": dict(
        template="Reach the upperbound of the world.",
        parameters=dict(),
    ),
    "race": dict(
        template="Race by {approach}.",
        parameters=dict(approach=["ice boat", "boat", "riding horse", "riding pig"]),
    ),
    "bring_in_nether": dict(
        template="Bring a {passive_mobs} into nether.",
        parameters=dict(passive_mobs=passive_mobs),
    ),
    "sail": dict(
        template="Sail on boat with a {passive_mobs}.",
        parameters=dict(passive_mobs=passive_mobs),
    ),
    "tame": dict(
        template="Tame a {tamable_animal}.",
        parameters=dict(tamable_animal=["horse", "wolf"]),
    ),
    "light_up": dict(
        template="light up a {architectures}.",
        parameters=dict(architectures=architectures_farm + ["cave"]),
    ),
    "clog": dict(
        template="Clog a {fluid_source}.",
        parameters=dict(fluid_source=["waterfall", "lava fall", "river"]),
    ),
    "climb": dict(
        template="Climb a waterfall.",
        parameters=dict(),
    ),
    "hook": dict(
        template="Hook a {mobs} using fishing rod.",
        parameters=dict(mobs=passive_mobs + hostile_mobs),
    ),
}
