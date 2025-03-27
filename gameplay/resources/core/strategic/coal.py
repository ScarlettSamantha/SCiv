from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDesert
from gameplay.terrain.flat_pine_forest import FlatPineForest
from gameplay.terrain.flat_savanna import FlatSavanna
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, _t


class Coal(BaseStrategicResource):
    key: str = "resource.core.strategic.coal"
    name: T_TranslationOrStr = _t("content.resources.core.coal.name")
    description: T_TranslationOrStr = _t("content.resources.core.coal.description")
    _color = (1.0, 0.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/strategic/bordered_coal.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatSavanna: 70.0,
        FlatDesert: 70.0,
        FlatScrubland: 70.0,
        FlatPineForest: 40.0,
        HillsDesert: 70.0,
        HillsTundra: 70.0,
    }
    coverage = 0.75
    spawn_amount = 3.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
