from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDesert
from gameplay.terrain.flat_jungle import FlatJungle
from gameplay.terrain.flat_savanna import FlatSavanna
from managers.i18n import T_TranslationOrStr, _t


class Murcury(BaseBonusResource):
    key: str = "resource.core.bonus.murcury"
    name: T_TranslationOrStr = _t("content.resources.core.murcury.name")
    description: T_TranslationOrStr = _t("content.resources.core.murcury.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/bordered_murcury.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatSavanna: 70.0,
        FlatJungle: 70.0,
        FlatDesert: 70.0,
    }
    spawn_amount = 5.0
    coverage = 0.3

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
