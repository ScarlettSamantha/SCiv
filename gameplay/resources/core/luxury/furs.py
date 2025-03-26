from typing import Dict, Type

from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Furs(BaseLuxuryResource):
    key: str = "resource.core.luxury.furs"
    name: T_TranslationOrStr = _t("content.resources.core.furs.name")
    description: T_TranslationOrStr = _t("content.resources.core.furs.description")
    icon: str = "assets/icons/resources/core/luxury/hex_border_furs.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 5.0
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
