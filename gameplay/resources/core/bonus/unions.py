from typing import Dict, Tuple, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Unions(BaseBonusResource):
    key: str = "resource.core.bonus.unions"
    name: T_TranslationOrStr = _t("content.resources.core.unions.name")
    description: T_TranslationOrStr = _t("content.resources.core.unions.description")
    icon: str = "assets/icons/resources/core/bonus/bordered_unions.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 6.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
