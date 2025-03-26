from typing import Dict, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.flat_tundra import FlatTundra
from gameplay.terrain.hills_grass import HillsGrass
from managers.i18n import T_TranslationOrStr, _t


class Cows(BaseBonusResource):
    key: str = "resource.core.bonus.cows"
    name: T_TranslationOrStr = _t("content.resources.core.cows.name")
    description: T_TranslationOrStr = _t("content.resources.core.cows.description")
    icon: str = "assets/icons/resources/core/bonus/bordered_cow.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatScrubland: 100.0,
        FlatGrass: 100.0,
        FlatTundra: 20.0,
        HillsGrass: 20.0,
    }
    coverage = 0.7
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
