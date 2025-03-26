from typing import Dict, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDessert
from gameplay.terrain.flat_tundra import FlatTundra
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, _t


class Iron(BaseBonusResource):
    key: str = "resource.core.bonus.iron"
    name: T_TranslationOrStr = _t("content.resources.core.iron.name")
    description: T_TranslationOrStr = _t("content.resources.core.iron.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_iron.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        HillsForest: 60.0,
        HillsGrass: 50.0,
        HillsTundra: 100.0,
        HillsDesert: 100.0,
        FlatTundra: 100.0,
        FlatDessert: 100.0,
    }
    spawn_amount = 5.0
    coverage = 0.6

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
