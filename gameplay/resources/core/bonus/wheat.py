from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.hills_grass import HillsGrass
from managers.i18n import T_TranslationOrStr, _t


class Wheat(BaseBonusResource):
    key: str = "resource.core.bonus.wheat"
    name: T_TranslationOrStr = _t("content.resources.core.wheat.name")
    description: T_TranslationOrStr = _t("content.resources.core.wheat.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/bordered_wheat.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {FlatGrass: 100.0, HillsGrass: 30.0, BaseTerrain: 0.0}
    coverage = 0.5
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
