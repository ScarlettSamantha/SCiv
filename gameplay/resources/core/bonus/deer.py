from typing import Dict, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, _t


class Deer(BaseBonusResource):
    key: str = "resource.core.bonus.deer"
    name: T_TranslationOrStr = _t("content.resources.core.deer.name")
    description: T_TranslationOrStr = _t("content.resources.core.deer.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_deer.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        HillsTundra: 70.0,
        HillsForest: 50.0,
        HillsGrass: 50.0,
        FlatForest: 50.0,
        FlatGrass: 40.0,
    }
    spawn_amount = 5.0
    coverage = 0.8

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
