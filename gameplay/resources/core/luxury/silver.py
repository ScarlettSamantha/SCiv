from typing import Dict, Type

from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Silver(BaseLuxuryResource):
    key: str = "resource.core.luxury.silver"
    name: T_TranslationOrStr = _t("content.resources.core.silver.name")
    description: T_TranslationOrStr = _t("content.resources.core.silver.description")
    icon: str = "assets/icons/resources/core/luxury/hex_border_silver.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 50.0
    spawn_amount = 5.0
    coverage = 0.35

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
