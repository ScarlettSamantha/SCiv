from typing import Dict, Type

from gameplay.improvements.core.resources.mine import Mine
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDesert
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_savanna import FlatSavanna
from gameplay.terrain.flat_tundra import FlatTundra
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.terrain.hills_snow import HillsSnow
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, t_


class RareEarthMetals(BaseStrategicResource):
    key: str = "resource.core.strategic.rare_earth_metals"
    name: T_TranslationOrStr = t_("content.resources.core.rare_earth_metals.name")
    description: T_TranslationOrStr = t_("content.resources.core.rare_earth_metals.description")
    _color = (1.0, 0.0, 0.0)
    icon: str = "assets/icons/default/resources/core/strategic/bordered_rare_earth_metals.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatGrass: 20.0,
        FlatDesert: 70.0,
        FlatSavanna: 70.0,
        FlatTundra: 70.0,
        HillsTundra: 70.0,
        HillsDesert: 70.0,
        HillsSnow: 70.0,
        HillsForest: 20.0,
        HillsGrass: 20.0,
    }
    spawn_amount = 3.0
    coverage = 0.5
    improvement_required = [Mine]

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
