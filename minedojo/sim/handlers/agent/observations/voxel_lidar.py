import numpy as np

from minedojo.sim import spaces
from minedojo.sim.handlers.translation import KeymapTranslationHandler


class VoxelObservation(KeymapTranslationHandler):
    """
    Handles voxel observations.
    Returned voxels are in (x, y, z) order, where x, y, z are all in ascending order.
    """

    def to_hero(self, x) -> str:
        pass

    def to_string(self):
        return "voxels"

    def xml_template(self) -> str:
        return str(
            """
            <ObservationFromGrid>                      
                <Grid name="voxels">                        
                    <min x="{{xmin}}" y="{{ymin}}" z="{{zmin}}"/>                        
                    <max x="{{xmax}}" y="{{ymax}}" z="{{zmax}}"/>                      
                </Grid>                  
            </ObservationFromGrid>"""
        )

    def __init__(self, limits=((-3, 3), (-1, 3), (-3, 3))):
        self.xmin = limits[0][0]
        self.ymin = limits[1][0]
        self.zmin = limits[2][0]
        self.xmax = limits[0][1]
        self.ymax = limits[1][1]
        self.zmax = limits[2][1]
        self.grid_size = [1 + b - a for a, b in limits]

        space = spaces.Dict(
            {
                "block_name": spaces.Text(shape=self.grid_size),
                # max block meta is 120, i.e., item id 383:120 spawn egg for villager
                # see https://minecraft-ids.grahamedgecombe.com/
                "block_meta": spaces.Box(
                    low=0, high=120, shape=self.grid_size, dtype=np.int64
                ),
                "is_collidable": spaces.Box(
                    low=0, high=1, shape=self.grid_size, dtype=bool
                ),
                "is_tool_not_required": spaces.Box(
                    low=0, high=1, shape=self.grid_size, dtype=bool
                ),
                "blocks_movement": spaces.Box(
                    low=0, high=1, shape=self.grid_size, dtype=bool
                ),
                "is_liquid": spaces.Box(
                    low=0, high=1, shape=self.grid_size, dtype=bool
                ),
                "is_solid": spaces.Box(low=0, high=1, shape=self.grid_size, dtype=bool),
                "can_burn": spaces.Box(low=0, high=1, shape=self.grid_size, dtype=bool),
                "blocks_light": spaces.Box(
                    low=0, high=1, shape=self.grid_size, dtype=bool
                ),
                "cos_look_vec_angle": spaces.Box(
                    low=-1, high=1, shape=self.grid_size, dtype=np.float32
                ),
            }
        )
        # gym.space.Dict will sort keys! So we keep the order by ourselves
        self._key_list = [
            "block_name",
            "block_meta",
            "is_collidable",
            "is_tool_not_required",
            "blocks_movement",
            "is_liquid",
            "is_solid",
            "can_burn",
            "blocks_light",
            "cos_look_vec_angle",
        ]
        super().__init__(hero_keys=["voxels"], univ_keys=["voxels"], space=space)

    def from_hero(self, obs):
        voxels_arr = obs[self.hero_keys[0]]
        assert len(voxels_arr) == np.prod(self.grid_size) * len(
            self._key_list
        ), "INTERNAL"
        # yunfan: note that returns from java side are in F order, we need to use F order to be consistent
        return {
            key: np.array(
                [
                    voxels_arr[i]
                    for i in range(bias, len(voxels_arr), len(self._key_list))
                ],
                dtype=self.space[key].dtype,
            ).reshape(self.space[key].shape, order="F")
            for bias, key in enumerate(self._key_list)
        }

    def __or__(self, other):
        """
        Combines two voxel observations into one. If all of the properties match return self
        otherwise raise an exception.
        """
        if (
            isinstance(other, VoxelObservation)
            and self.grid_min == other.grid_min
            and self.grid_max == other.grid_max
        ):
            return self
        else:
            raise ValueError("Incompatible observables!")


class RichLidarObservation(KeymapTranslationHandler):
    """
    Handles rich LIDAR observations.
    """

    def to_hero(self, x) -> str:
        pass

    def to_string(self):
        return "rays"

    def xml_template(self) -> str:
        return str(
            """
            <ObservationFromRichLidar>
                {% for ray in rays %}
                    <RayOffset pitch="{{ray[0]}}" yaw="{{ray[1]}}" distance="{{ray[2]}}"/>
                {% endfor %}
            </ObservationFromRichLidar>
        """
        )

    def __init__(self, rays=None):
        # Note rays use [pitch, yaw, distance]:
        # The pitch (in radians) is relative to lookVec
        # The yaw (in radians) is relative to lookVec
        # The distance (in meters) is the maximum distance for the ray from eyePos

        if rays is None:
            rays = [
                (0.0, 0.0, 10.0),
            ]
        self.rays = rays
        self.num_rays = len(rays)

        _shape = [self.num_rays]
        space = spaces.Dict(
            {
                "block_name": spaces.Text(shape=_shape),
                "block_distance": spaces.Box(
                    low=-1, high=np.inf, shape=_shape, dtype=np.float32
                ),
                # max block meta is 120, i.e., item id 383:120 spawn egg for villager
                # see https://minecraft-ids.grahamedgecombe.com/
                "block_meta": spaces.Box(low=0, high=120, shape=_shape, dtype=np.int64),
                "harvest_level": spaces.Box(
                    low=-1, high=4, shape=_shape, dtype=np.int64
                ),
                "is_tool_not_required": spaces.Box(
                    low=0, high=1, shape=_shape, dtype=bool
                ),
                "blocks_movement": spaces.Box(low=0, high=1, shape=_shape, dtype=bool),
                "is_liquid": spaces.Box(low=0, high=1, shape=_shape, dtype=bool),
                "is_solid": spaces.Box(low=0, high=1, shape=_shape, dtype=bool),
                "can_burn": spaces.Box(low=0, high=1, shape=_shape, dtype=bool),
                "entity_name": spaces.Text(shape=_shape),
                "entity_distance": spaces.Box(
                    low=-1, high=np.inf, shape=_shape, dtype=np.float32
                ),
                "ray_pitch": spaces.Box(
                    low=-np.inf, high=np.inf, shape=_shape, dtype=np.float32
                ),
                "ray_yaw": spaces.Box(
                    low=-np.inf, high=np.inf, shape=_shape, dtype=np.float32
                ),
                "traced_block_x": spaces.Box(
                    low=-np.inf, high=np.inf, shape=_shape, dtype=np.float32
                ),
                "traced_block_y": spaces.Box(
                    low=-np.inf, high=np.inf, shape=_shape, dtype=np.float32
                ),
                "traced_block_z": spaces.Box(
                    low=-np.inf, high=np.inf, shape=_shape, dtype=np.float32
                ),
            }
        )
        # gym.space.Dict will sort keys! So we keep the order by ourselves
        self._key_list = [
            "block_name",
            "block_distance",
            "block_meta",
            "harvest_level",
            "is_tool_not_required",
            "blocks_movement",
            "is_liquid",
            "is_solid",
            "can_burn",
            "entity_name",
            "entity_distance",
            "ray_pitch",
            "ray_yaw",
            "traced_block_x",
            "traced_block_y",
            "traced_block_z",
        ]

        super().__init__(
            hero_keys=["rays"],
            univ_keys=["rays"],
            space=space,
        )

    def from_hero(self, obs):
        raytrace_arr = obs[self.hero_keys[0]]
        assert len(raytrace_arr) == self.num_rays * len(self._key_list), "INTERNAL"
        return {
            key: np.array(
                [
                    self._map_entity_name(raytrace_arr[i])
                    if key == "entity_name"
                    else raytrace_arr[i]
                    for i in range(bias, len(raytrace_arr), len(self._key_list))
                ],
                dtype=self.space[key].dtype,
            ).reshape(self.space[key].shape)
            for bias, key in enumerate(self._key_list)
        }

    def __or__(self, other):
        """
        Combines two rich lidar observations into one.
        """
        if isinstance(other, RichLidarObservation):
            all_rays = self.rays + other.rays
            return RichLidarObservation(rays=all_rays)
        else:
            raise ValueError("Incompatible observables!")

    @staticmethod
    def _map_entity_name(raw_name: str) -> str:
        if raw_name.startswith("Entity"):
            return raw_name[6:].lower()
        elif raw_name == "null":
            return raw_name
        else:
            print(f"Unknown entity prefix. Return raw name {raw_name}")
            return raw_name
