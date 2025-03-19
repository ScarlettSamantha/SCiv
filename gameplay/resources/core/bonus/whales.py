from typing import Dict, Tuple, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Whales(BaseBonusResource):
    key: str = "resource.core.bonus.whales"
    name: T_TranslationOrStr = _t("content.resources.core.whales.name")
    description: T_TranslationOrStr = _t("content.resources.core.whales.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_whales.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 8.0
    spawn_amount: float | Tuple[float, float] = 5.0
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.WATER

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
