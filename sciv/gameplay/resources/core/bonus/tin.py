from typing import Dict, Type

from gameplay.improvements.core.resources.mine import Mine
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_heavy_forest import FlatHeavyForest
from gameplay.terrain.flat_pine_forest import FlatPineForest
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.terrain.hills_snow import HillsSnow
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, t_


class Tin(BaseBonusResource):
    key: str = "resource.core.bonus.tin"
    name: T_TranslationOrStr = t_("content.resources.core.tin.name")
    description: T_TranslationOrStr = t_("content.resources.core.tin.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/hex_border_tin.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        FlatForest: 20.0,
        FlatGrass: 20.0,
        FlatHeavyForest: 20.0,
        BaseTerrain: 0.0,
        HillsForest: 50.0,
        HillsGrass: 50.0,
        HillsTundra: 70.0,
        HillsSnow: 70.0,
        FlatPineForest: 50.0,
    }
    spawn_amount = 5.0
    coverage = 0.5
    improvement_required = [Mine]
    model = "assets/models/resources/stack_tin_bars.glb"
    model_size = 0.25

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
