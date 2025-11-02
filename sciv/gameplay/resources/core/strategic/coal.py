from typing import Dict, Type

from gameplay.improvements.core.resources.mine import Mine
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_pine_forest import FlatPineForest
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_snow import HillsSnow
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, t_


class Coal(BaseStrategicResource):
    key: str = "resource.core.strategic.coal"
    name: T_TranslationOrStr = t_("content.resources.core.coal.name")
    description: T_TranslationOrStr = t_("content.resources.core.coal.description")
    _color = (1.0, 0.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/default/resources/core/strategic/bordered_coal.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatScrubland: 70.0,
        FlatPineForest: 40.0,
        HillsTundra: 70.0,
        HillsForest: 50.0,
        HillsSnow: 30.0,
        HillsDesert: 20.0,
    }
    coverage = 0.75
    spawn_amount = 3.0
    improvement_required = [Mine]
    model = ("assets/models/resources/pile_coal.glb", None)
    model_size = 0.33

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
