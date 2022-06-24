# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import numpy as np

import minedojo.sim.mc_meta.mc as mc
import minedojo.sim.spaces as spaces
from minedojo.sim.handlers.translation import (
    KeymapTranslationHandler,
    TranslationHandlerGroup,
)


__all__ = ["ObservationFromLifeStats"]


class ObservationFromLifeStats(TranslationHandlerGroup):
    """Groups all lifestats observations together to correspond to one XML element."""

    def to_string(self) -> str:
        return "life_stats"

    def __init__(self):
        super(ObservationFromLifeStats, self).__init__(
            handlers=[
                _LifeObservation(),
                _ArmorObservation(),
                _FoodObservation(),
                _SaturationObservation(),
                _XPObservation(),
                _BreathObservation(),
                _IsSleepingObservation(),
            ]
        )

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")


class LifeStatsObservation(KeymapTranslationHandler):
    def to_hero(self, x) -> str:
        pass

    def __init__(self, hero_keys, univ_keys, space, default_if_missing=None):
        self.hero_keys = hero_keys
        self.univ_keys = univ_keys
        super().__init__(
            hero_keys=hero_keys,
            univ_keys=["life_stats"] + univ_keys,
            space=space,
            default_if_missing=default_if_missing,
        )

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")


class _LifeObservation(LifeStatsObservation):
    """
    Handles life observation / health observation. Its initial value on world creation is 20 (full bar)
    """

    def __init__(self):
        keys = ["life"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Box(low=0, high=mc.MAX_LIFE, shape=(1,), dtype=np.float32),
            default_if_missing=mc.MAX_LIFE,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _ArmorObservation(LifeStatsObservation):
    """
    Handles life observation / armor observation. Its initial value on world creation is 0 (wearing no armors)
    """

    def __init__(self):
        keys = ["armor"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Box(low=0, high=mc.MAX_ARMOR, shape=(1,), dtype=np.float32),
            default_if_missing=0,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _FoodObservation(LifeStatsObservation):
    """
    Handles food_level observation representing the player's current hunger level, shown on the hunger bar. Its initial
    value on world creation is 20 (full bar) - https://minecraft.gamepedia.com/Hunger#Mechanics
    """

    def __init__(self):
        super().__init__(
            hero_keys=["food"],
            univ_keys=["food"],
            space=spaces.Box(low=0, high=mc.MAX_FOOD, shape=(1,), dtype=np.float32),
            default_if_missing=mc.MAX_FOOD,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _SaturationObservation(LifeStatsObservation):
    """
    Returns the food saturation observation which determines how fast the hunger level depletes and is controlled by the
    kinds of food the player has eaten. Its maximum value always equals foodLevel's value and decreases with the hunger
    level. Its initial value on world creation is 5. - https://minecraft.gamepedia.com/Hunger#Mechanics
    """

    def __init__(self):
        super().__init__(
            hero_keys=["saturation"],
            univ_keys=["saturation"],
            space=spaces.Box(
                low=0, high=mc.MAX_FOOD_SATURATION, shape=(1,), dtype=np.float32
            ),
            default_if_missing=5.0,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _XPObservation(LifeStatsObservation):
    """
    Handles observation of experience points 1395 experience corresponds with level 30
    - see https://minecraft.gamepedia.com/Experience for more details
    """

    def __init__(self):
        keys = ["xp"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Box(low=0, high=mc.MAX_XP, shape=(1,), dtype=np.float32),
            default_if_missing=0,
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _BreathObservation(LifeStatsObservation):
    """
    Handles observation of breath which tracks the amount of air remaining before beginning to suffocate
    """

    def __init__(self):
        super().__init__(
            hero_keys=["air"],
            univ_keys=["air"],
            space=spaces.Box(low=0, high=mc.MAX_BREATH, shape=(1,), dtype=np.float32),
            default_if_missing=300,
        )

    def to_string(self) -> str:
        return "oxygen"

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _IsSleepingObservation(LifeStatsObservation):
    def __init__(self):
        super().__init__(
            hero_keys=["is_sleeping"],
            univ_keys=["is_sleeping"],
            space=spaces.Discrete(2),
            default_if_missing=0,
        )


class _IsAliveObservation(LifeStatsObservation):
    def __init__(self):
        keys = ["is_alive"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Discrete(2),
            default_if_missing=1,
        )
