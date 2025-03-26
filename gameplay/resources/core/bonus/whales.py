from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.coast import Coast
from gameplay.terrain.sea import Sea
from gameplay.terrain.sea_ice import SeaIce
from managers.i18n import T_TranslationOrStr, _t


class Whales(BaseBonusResource):
    key: str = "resource.core.bonus.whales"
    name: T_TranslationOrStr = _t("content.resources.core.whales.name")
    description: T_TranslationOrStr = _t("content.resources.core.whales.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_whales.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {SeaIce: 0.0, Sea: 100.0, Coast: 40.0}
    coverage = 0.9
    spawn_amount = 5.0
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.WATER

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
