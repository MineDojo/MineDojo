# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
from typing import List

import numpy as np

from minedojo.sim import spaces
from minedojo.sim.handlers.translation import (
    KeymapTranslationHandler,
    TranslationHandlerGroup,
)


__all__ = ["ObservationFromCurrentLocation"]


class ObservationFromCurrentLocation(TranslationHandlerGroup):
    """
    Includes the current biome, how likely rain and snow are there, as well as the current light level, how bright the
    sky is, and if the player can see the sky.

    Also includes x, y, z, roll, and pitch
    """

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")

    def to_string(self) -> str:
        return "location_stats"

    def __init__(self):
        super(ObservationFromCurrentLocation, self).__init__(
            handlers=[
                _SunBrightnessObservation(),
                _SkyLightLevelObservation(),
                _LightLevelObservation(),
                _CanSeeSkyObservation(),
                _BiomeRainfallObservation(),
                _BiomeTemperatureObservation(),
                _IsRainingObservation(),
                # TODO _BiomeNameObservation(),
                _BiomeIDObservation(),
                _PitchObservation(),
                _YawObservation(),
                _SeaLevelObservation(),
                _PosObservation(),
            ]
        )


class _PosObservation(KeymapTranslationHandler):
    def __init__(self):
        keys = ["xpos", "ypos", "zpos"]
        space = spaces.Box(low=-640000.0, high=640000.0, shape=(3,), dtype=np.float32)
        default = np.array([0.0, 0.0, 0.0])
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=space,
            default_if_missing=default,
            to_string="pos",
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.array(
            [hero_dict["xpos"], hero_dict["ypos"], hero_dict["zpos"]],
            dtype=self.space.dtype,
        )


class _FullStatsObservation(KeymapTranslationHandler):
    def to_hero(self, x) -> int:
        for key in self.hero_keys:
            x = x[key]
        return x

    def __init__(self, key_list: List[str], space=None, default_if_missing=None):
        if space is None:
            if "achievement" == key_list[0]:
                space = spaces.Box(low=0, high=1, shape=(), dtype=np.int)
            else:
                space = spaces.Box(low=0, high=np.inf, shape=(), dtype=np.int)
        if default_if_missing is None:
            default_if_missing = np.zeros((), dtype=np.float)

        super().__init__(
            hero_keys=key_list,
            univ_keys=key_list,
            space=space,
            default_if_missing=default_if_missing,
        )

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")


class _SunBrightnessObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["sun_brightness"],
            space=spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32),
            default_if_missing=0.94,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _SkyLightLevelObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["sky_light_level"],
            space=spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32),
            default_if_missing=0.71,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _PitchObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["pitch"],
            space=spaces.Box(low=-180.0, high=180.0, shape=(1,), dtype=np.float32),
            default_if_missing=0.0,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _YawObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["yaw"],
            space=spaces.Box(low=-180.0, high=180.0, shape=(1,), dtype=np.float32),
            default_if_missing=0.0,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _BiomeIDObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["biome_id"],
            space=spaces.Box(low=0, high=167, shape=(), dtype=int),
            default_if_missing=0,
        )


class _BiomeRainfallObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["biome_rainfall"],
            space=spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32),
            default_if_missing=0.5,
        )

    def to_string(self) -> str:
        return "rainfall"

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _BiomeTemperatureObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["biome_temperature"],
            space=spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32),
            default_if_missing=0.5,
        )

    def to_string(self) -> str:
        return "temperature"

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _SeaLevelObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["sea_level"],
            space=spaces.Box(low=0.0, high=255, shape=(1,), dtype=np.float32),
            default_if_missing=63,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _LightLevelObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["light_level"],
            space=spaces.Box(low=0.0, high=15, shape=(1,), dtype=np.float32),
            default_if_missing=15,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _IsRainingObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(
            key_list=["is_raining"],
            space=spaces.Box(low=0, high=1, shape=(), dtype=int),
            default_if_missing=0,
        )


class _CanSeeSkyObservation(_FullStatsObservation):
    def to_hero(self, x):
        for key in self.hero_keys:
            x = x[key]
        return np.eye(2)[x]

    def __init__(self):
        super().__init__(
            key_list=["can_see_sky"],
            space=spaces.Box(low=0, high=1, shape=(), dtype=int),
            default_if_missing=1,
        )
