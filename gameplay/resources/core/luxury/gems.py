from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from managers.i18n import T_TranslationOrStr, _t


class Gems(BaseLuxuryResource):
    key: str = "resource.core.luxury.gems"
    name: T_TranslationOrStr = _t("content.resources.core.gems.name")
    description: T_TranslationOrStr = _t("content.resources.core.gems.description")
    icon: str = "assets/icons/resources/core/luxury/hex_border_gems.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 15.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
