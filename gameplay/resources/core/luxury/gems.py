from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Gems(BaseLuxuryResource):
    key: str = "resource.core.luxury.gems"
    name: T_TranslationOrStr = _t("content.resources.core.gems.name")
    description: T_TranslationOrStr = _t("content.resources.core.gems.description")
    _color = (1.0, 1.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/luxury/hex_border_gems.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 15.0
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
