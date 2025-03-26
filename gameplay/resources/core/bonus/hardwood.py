from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_heavy_forest import FlatHeavyForest
from gameplay.terrain.flat_jungle import FlatJungle
from gameplay.terrain.hills_forest import HillsForest
from managers.i18n import T_TranslationOrStr, _t


class Hardwood(BaseBonusResource):
    key: str = "resource.core.bonus.hardwood"
    name: T_TranslationOrStr = _t("content.resources.core.hardwood.name")
    description: T_TranslationOrStr = _t("content.resources.core.hardwood.description")
    _color = (1.0, 0.0, 1.0)
    icon: str = "assets/icons/resources/core/bonus/hex_border_hardwood.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatForest: 70.0,
        FlatHeavyForest: 70.0,
        FlatJungle: 70.0,
        HillsForest: 70.0,
    }
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    coverage = 1.0
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
