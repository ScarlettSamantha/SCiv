from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Marble(BaseBonusResource):
    key: str = "resource.core.bonus.marble"
    name: T_TranslationOrStr = _t("content.resources.core.marble.name")
    description: T_TranslationOrStr = _t("content.resources.core.marble.description")
    _color = (1.0, 0.0, 1.0)
    icon: str = "assets/icons/resources/core/bonus/hex_border_marble.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 100
    spawn_amount = 5.0
    coverage = 0.3

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
