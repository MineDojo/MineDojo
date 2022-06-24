# Copyright (c) 2021 All Rights Reserved
# Author: Brandon Houghton
from typing import List

import numpy as np

from minedojo.sim import spaces
from minedojo.sim.handlers.translation import (
    KeymapTranslationHandler,
    TranslationHandlerGroup,
)


__all__ = ["ObservationFromDamageSource"]


class ObservationFromDamageSource(TranslationHandlerGroup):
    """
    Includes the most recent damage event including the amount, type, location, and
    other properties.
    """

    def xml_template(self) -> str:
        return ""

    def to_string(self) -> str:
        return "damage_source"

    def __init__(self):
        super().__init__(
            handlers=[
                _DamageAmount(),
                _DamageDistance(),
                _DamagePitch(),
                _DamageYaw(),
                _HungerDamage(),
                _IsExplosion(),
                _IsFire(),
                _IsMagic(),
                _IsProjectile(),
                _IsUnblockable(),
            ]
        )


class _DamageSourceProperty(KeymapTranslationHandler):
    def to_hero(self, x) -> int:
        for key in self.hero_keys:
            x = x[key]
        return x

    def __init__(self, key_list: List[str], space=None, default_if_missing=None):
        if space is None:
            space = spaces.Box(low=0, high=np.inf, shape=(), dtype=np.int)
        if default_if_missing is None:
            default_if_missing = np.zeros((), dtype=space.dtype)

        super().__init__(
            hero_keys=key_list,
            univ_keys=key_list,
            space=space,
            default_if_missing=default_if_missing,
            ignore_missing=True,
        )

    def xml_template(self) -> str:
        return ""


class _DamageAmount(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["damage_amount"],
            space=spaces.Box(low=0.0, high=40.0, shape=(1,), dtype=np.float32),
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _DamageDistance(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["damage_distance"],
            space=spaces.Box(low=0.0, high=np.inf, shape=(1,), dtype=np.float32),
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _HungerDamage(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["hunger_damage"],
            space=spaces.Box(low=0, high=20, shape=(1,), dtype=np.float32),
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _DamagePitch(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["damage_pitch"],
            space=spaces.Box(low=-90, high=90, shape=(1,), dtype=np.float32),
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _DamageYaw(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["damage_yaw"],
            space=spaces.Box(low=-180, high=180, shape=(1,), dtype=np.float32),
        )

    def from_hero(self, hero_dict, dtype=None):
        return np.expand_dims(super().from_hero(hero_dict, dtype), axis=0).astype(
            self.space.dtype
        )


class _IsExplosion(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["is_explosion"],
            space=spaces.Box(low=0, high=1, shape=(), dtype=bool),
        )


class _IsFire(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["is_fire_damage"],
            space=spaces.Box(low=0, high=1, shape=(), dtype=bool),
        )


class _IsMagic(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["is_magic_damage"],
            space=spaces.Box(low=0, high=1, shape=(), dtype=bool),
        )


class _IsProjectile(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["is_projectile"],
            space=spaces.Box(low=0, high=1, shape=(), dtype=bool),
        )


class _IsUnblockable(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=["is_unblockable"],
            space=spaces.Box(low=0, high=1, shape=(), dtype=bool),
        )
