from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDesert
from gameplay.terrain.flat_savanna import FlatSavanna
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.flat_tundra import FlatTundra
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_snow import HillsSnow
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, _t


class Uranium(BaseStrategicResource):
    key: str = "resource.core.strategic.uranium"
    name: T_TranslationOrStr = _t("content.resources.core.uranium.name")
    description: T_TranslationOrStr = _t("content.resources.core.uranium.description")
    _color = (1.0, 0.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/strategic/bordered_uranium.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatDesert: 70.0,
        FlatSavanna: 70.0,
        FlatTundra: 70.0,
        FlatScrubland: 30.0,
        HillsTundra: 70.0,
        HillsDesert: 70.0,
        HillsSnow: 70.0,
    }
    spawn_amount = 3.0
    coverage = 0.7

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
