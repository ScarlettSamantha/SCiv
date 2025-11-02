from typing import Dict, Type

from gameplay.improvements.core.resources.farm import Farm
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.hills_forest import HillsForest
from gameplay.tiles.hills_forest import HillsForestTerrain
from managers.i18n import T_TranslationOrStr, t_


class Berries(BaseBonusResource):
    key: str = "resource.core.bonus.berries"
    name: T_TranslationOrStr = t_("content.resources.core.berries.name")
    description: T_TranslationOrStr = t_("content.resources.core.berries.description")
    _color = (1.0, 0.0, 1.0)
    icon: str = "assets/icons/default/resources/core/bonus/hex_border_berries.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        FlatGrass: 70.0,
        FlatForest: 60.0,
        HillsForest: 60.0,
        HillsForestTerrain: 40.0,
    }
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    spawn_amount = 5.0
    improvement_required = [Farm]
    model = "assets/models/resources/crate_berries.glb"
    model_size = 0.75
    coverage = 0.7

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
