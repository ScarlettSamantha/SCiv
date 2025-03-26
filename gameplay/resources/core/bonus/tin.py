from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_pine_forest import FlatPineForest
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.terrain.hills_snow import HillsSnow
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, _t


class Tin(BaseBonusResource):
    key: str = "resource.core.bonus.tin"
    name: T_TranslationOrStr = _t("content.resources.core.tin.name")
    description: T_TranslationOrStr = _t("content.resources.core.tin.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/hex_border_tin.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        HillsForest: 50.0,
        HillsGrass: 50.0,
        HillsTundra: 70.0,
        HillsSnow: 70.0,
        FlatPineForest: 50.0,
    }
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
