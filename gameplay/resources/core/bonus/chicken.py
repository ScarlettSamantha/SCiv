from typing import Dict, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.flat_tundra import FlatTundra
from gameplay.terrain.hills_forest import HillsForest
from managers.i18n import T_TranslationOrStr, _t


class Chicken(BaseBonusResource):
    key: str = "resource.core.bonus.chicken"
    name: T_TranslationOrStr = _t("content.resources.core.chicken.name")
    description: T_TranslationOrStr = _t("content.resources.core.chicken.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_chicken.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatScrubland: 70.0,
        FlatGrass: 40.0,
        FlatForest: 40.0,
        HillsForest: 40.0,
        FlatTundra: 30.0,
    }
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
