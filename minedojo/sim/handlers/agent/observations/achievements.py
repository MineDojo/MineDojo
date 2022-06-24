from typing import Dict, Any

from minedojo.sim import spaces
from minedojo.sim.mc_meta.mc import ALL_ACHIEVEMENTS
from minedojo.sim.handlers.translation import TranslationHandler


class ObsFromAchievements(TranslationHandler):
    def to_string(self) -> str:
        return "achievements"

    def xml_template(self) -> str:
        return "<ObservationFromAchievements/>"

    def __init__(self):
        super().__init__(
            space=spaces.Dict(
                {achievement: spaces.Discrete(n=2) for achievement in ALL_ACHIEVEMENTS}
            )
        )

    def from_hero(self, x: Dict[str, Any]):
        return {k: int(v) for k, v in x[self.to_string()].items()}
