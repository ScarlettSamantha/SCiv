from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from managers.i18n import T_TranslationOrStr, _t


class Diamonds(BaseLuxuryResource):
    key: str = "resource.core.luxury.diamonds"
    name: T_TranslationOrStr = _t("content.resources.core.diamonds.name")
    description: T_TranslationOrStr = _t("content.resources.core.diamonds.description")
    icon: str = "assets/icons/resources/core/luxury/bordered_diamonds.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 15.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
