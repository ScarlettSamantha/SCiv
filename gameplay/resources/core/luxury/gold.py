from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from managers.i18n import T_TranslationOrStr, _t


class Gold(BaseLuxuryResource):
    key: str = "resource.core.luxury.gold"
    name: T_TranslationOrStr = _t("content.resources.core.gold.name")
    description: T_TranslationOrStr = _t("content.resources.core.gold.description")
    _color = (1.0, 1.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/luxury/bordered_gold.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        HillsGrass: 100.0,
        HillsDesert: 30.0,
        HillsForest: 80.0,
    }
    spawn_amount = 3.0
    coverage = 0.3

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
