from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Stone(BaseBonusResource):
    key: str = "resource.core.bonus.stone"
    name: T_TranslationOrStr = _t("content.resources.core.stone.name")
    description: T_TranslationOrStr = _t("content.resources.core.stone.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/hex_border_stone.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 100
    coverage = 0.4
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
