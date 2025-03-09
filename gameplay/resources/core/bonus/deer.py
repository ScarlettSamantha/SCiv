from typing import Dict, Tuple, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Deer(BaseBonusResource):
    key: str = "resource.core.bonus.deer"
    name: T_TranslationOrStr = _t("content.resources.core.deer.name")
    description: T_TranslationOrStr = _t("content.resources.core.deer.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_deer.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 5.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
