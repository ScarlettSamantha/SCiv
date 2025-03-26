from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Pearls(BaseLuxuryResource):
    key: str = "resource.core.luxury.pearls"
    name: T_TranslationOrStr = _t("content.resources.core.pearls.name")
    description: T_TranslationOrStr = _t("content.resources.core.pearls.description")
    icon: str = "assets/icons/resources/core/luxury/bordered_pearls.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 15.0
    spawn_amount = 5.0
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.WATER

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
