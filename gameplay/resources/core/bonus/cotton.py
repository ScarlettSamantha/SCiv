from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.hills_grass import HillsGrass
from managers.i18n import T_TranslationOrStr, _t


class Cotton(BaseBonusResource):
    key: str = "resource.core.bonus.cotton"
    name: T_TranslationOrStr = _t("content.resources.core.cotton.name")
    description: T_TranslationOrStr = _t("content.resources.core.cotton.description")
    _color = (1.0, 0.0, 1.0)
    icon: str = "assets/icons/resources/core/bonus/hex_border_cotton.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {BaseTerrain: 0.0, FlatGrass: 100.0, HillsGrass: 50.0}
    coverage = 0.5
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
