from typing import Dict, Type

from gameplay.improvements.core.resources.quarry import Quarry
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from managers.i18n import T_TranslationOrStr, t_


class Stone(BaseBonusResource):
    key: str = "resource.core.bonus.stone"
    name: T_TranslationOrStr = t_("content.resources.core.stone.name")
    description: T_TranslationOrStr = t_("content.resources.core.stone.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/hex_border_stone.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 100
    coverage = 0.4
    spawn_amount = 5.0
    improvement_required = [Quarry]
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        HillsGrass: 100.0,
        HillsDesert: 30.0,
        HillsForest: 80.0,
    }
    model = "assets/models/resources/stack_stone.glb"
    model_size = 0.20

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
