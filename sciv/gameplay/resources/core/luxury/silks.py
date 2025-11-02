from typing import Dict, Type

from gameplay.improvements.core.resources.farm import Farm
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_heavy_forest import FlatHeavyForest
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from managers.i18n import T_TranslationOrStr, t_


class Silk(BaseLuxuryResource):
    key: str = "resource.core.luxury.silk"
    name: T_TranslationOrStr = t_("content.resources.core.silk.name")
    description: T_TranslationOrStr = t_("content.resources.core.silk.description")
    _color = (1.0, 1.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/default/resources/core/luxury/hex_border_silk.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        FlatGrass: 60.0,
        HillsGrass: 60.0,
        HillsForest: 80.0,
        FlatForest: 60.0,
        FlatHeavyForest: 50.0,
        FlatScrubland: 70.0,
    }
    spawn_amount = 5.0
    coverage = 0.35
    improvement_required = [Farm]
    model = "assets/models/resources/stack_cloth.glb"
    model_size = 0.25

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
