from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDessert
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_tundra import FlatTundra
from managers.i18n import T_TranslationOrStr, _t


class Onions(BaseBonusResource):
    key: str = "resource.core.bonus.onions"
    name: T_TranslationOrStr = _t("content.resources.core.onions.name")
    description: T_TranslationOrStr = _t("content.resources.core.onions.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/bordered_onions.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatTundra: 40.0,
        FlatForest: 40.0,
        FlatDessert: 40.0,
    }
    coverage = 0.7
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
