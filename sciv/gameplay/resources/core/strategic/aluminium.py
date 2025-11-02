from typing import Dict, Type

from gameplay.improvements.core.resources.mine import Mine
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDesert
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_pine_forest import FlatPineForest
from gameplay.terrain.flat_savanna import FlatSavanna
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_snow import HillsSnow
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, t_


class Aluminium(BaseStrategicResource):
    key: str = "resource.core.strategic.aluminium"
    name: T_TranslationOrStr = t_("content.resources.core.aluminium.name")
    description: T_TranslationOrStr = t_("content.resources.core.aluminium.description")
    _color = (1.0, 0.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/default/resources/core/strategic/bordered_rare_earth_rods.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        HillsForest: 100.0,
        HillsSnow: 100.0,
        HillsTundra: 100.0,
        FlatForest: 40.0,
        FlatScrubland: 70.0,
        FlatDesert: 70.0,
        FlatSavanna: 70.0,
        FlatPineForest: 40.0,
    }
    spawn_amount = 5.0
    coverage = 1.1
    improvement_required = [Mine]

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
