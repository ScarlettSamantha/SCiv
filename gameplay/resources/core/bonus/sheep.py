from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_scrubland import FlatScrubland
from managers.i18n import T_TranslationOrStr, _t


class Sheep(BaseBonusResource):
    key: str = "resource.core.bonus.sheep"
    name: T_TranslationOrStr = _t("content.resources.core.sheep.name")
    description: T_TranslationOrStr = _t("content.resources.core.sheep.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/bordered_sheep.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatGrass: 100.0,
        FlatForest: 40.0,
        FlatScrubland: 100.0,
    }
    spawn_amount = 5.0
    coverage = 1.1

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
