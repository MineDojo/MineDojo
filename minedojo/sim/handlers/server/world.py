# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""
World handlers provide a number of ways to generate and modify the Minecraft world
(e.g. specifying the type of world to be created, like Superflat, or drawing shapes and blocks in the world).

When used to create a Gym environment, they should be passed to :code:`create_server_world_generators`
"""

from typing import Union
from minedojo.sim.mc_meta import mc
from minedojo.sim.handler import Handler


class DefaultWorldGenerator(Handler):
    """Generates a world using minecraft procedural generation (this is the default world type in minecraft).

    Args:
        force_reset (bool, optional): If the world should be reset every episode.. Defaults to True.
        world_seed: https://minecraft.fandom.com/wiki/Seed_(level_generation)

    Example usage:

    .. code-block:: python

        # Generates a default world that does not reset every episode (e.g. if blocks get broken in one episode
        # they will not be replaced in the next)
        DefaultWorldGenerator(False, "")
    """

    def to_string(self) -> str:
        return "default_world_generator"

    def xml_template(self) -> str:
        return str(
            """<DefaultWorldGenerator
                forceReset="{{force_reset | string | lower}}"
                seed="{{world_seed}}"
                generatorOptions="{}"/>
            """
        )

    def __init__(self, force_reset=True, world_seed: str = ""):
        self.force_reset = force_reset
        self.world_seed = world_seed


class FileWorldGenerator(Handler):
    """Generates a world from a file."""

    def to_string(self) -> str:
        return "file_world_generator"

    def xml_template(self) -> str:
        return str(
            """<FileWorldGenerator
                destroyAfterUse = "{{destroy_after_use | string | lower}}"
                src = "{{filename}}" />
            """
        )

    def __init__(self, filename: str, destroy_after_use: bool = True):
        self.filename = filename
        self.destroy_after_use = destroy_after_use


#  <FlatWorldGenerator forceReset="true"/>
class FlatWorldGenerator(Handler):
    """
    Generates a world that is a flat landscape.

    Example usage:

    .. code-block:: python
        # Create a superflat world with layers as follow:
        # 1 layer of grass blocks above 2 layers of dirt above 1 layer of bedrock
        # You can use websites like "`Minecraft Tools`_" to easily customize superflat world layers.
        FlatWorldGenerator(generatorString="1;7,2x3,2;1")

    .. _Minecraft Tools: https://minecraft.tools/en/flat.php?biome=1&bloc_1_nb=1&bloc_1_id=2&bloc_2_nb=2&bloc_2_id=3%2F00&bloc_3_nb=1&bloc_3_id=7&village_size=1&village_distance=32&mineshaft_chance=1&stronghold_count=3&stronghold_distance=32&stronghold_spread=3&oceanmonument_spacing=32&oceanmonument_separation=5&biome_1_distance=32&valid=Create+the+Preset#seed
    """

    def to_string(self) -> str:
        return "flat_world_generator"

    def xml_template(self) -> str:
        return str(
            """<FlatWorldGenerator
                forceReset="{{force_reset | string | lower}}"
                generatorString="{{generatorString}}" />
            """
        )

    def __init__(self, force_reset: bool = True, generatorString: str = ""):
        self.force_reset = force_reset
        self.generatorString = generatorString


#  <BiomeGenerator forceReset="true" biome="3"/>
class BiomeGenerator(Handler):
    def to_string(self) -> str:
        return "biome_generator"

    def xml_template(self) -> str:
        return str(
            """<BiomeGenerator
                forceReset="{{force_reset | string | lower}}"
                seed="{{world_seed}}"
                biome="{{biome_id}}" />
            """
        )

    def __init__(
        self, biome: Union[int, str], force_reset: bool = True, world_seed: str = ""
    ):
        if isinstance(biome, str):
            biome = mc.BIOMES_MAP[biome]
        self.biome_id = biome
        self.force_reset = force_reset
        self.world_seed = world_seed


class DrawingDecorator(Handler):
    """
    Draws shapes (e.g. spheres, cuboids) in the world.

    Example usage:

    .. code-block:: python

        # draws an empty square of gold blocks
        DrawingDecorator('
            <DrawCuboid x1="3" y1="4" z1="3" x2="3" y2="6" z2="-3" type="gold_block"/>
            <DrawCuboid x1="3" y1="4" z1="3" x2="-3" y2="6" z2="3" type="gold_block"/>
            <DrawCuboid x1="-3" y1="4" z1="-3" x2="3" y2="6" z2="-3" type="gold_block"/>
            <DrawCuboid x1="-3" y1="4" z1="-3" x2="-3" y2="6" z2="3" type="gold_block"/>
        ')

    See Project Malmo for more
    """

    def __init__(self, to_draw: str):
        self.to_draw = to_draw

    def xml_template(self) -> str:
        tmp = """<DrawingDecorator>{{to_draw}}</DrawingDecorator>"""
        return tmp

    def to_string(self) -> str:
        return "drawing_decorator"


class VillageSpawnDecorator(Handler):
    def xml_template(self) -> str:
        tmp = """<VillageSpawnDecorator />"""
        return tmp

    def to_string(self) -> str:
        return "village_spawn"
