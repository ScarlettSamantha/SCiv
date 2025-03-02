from typing import Tuple, Dict, Type
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from managers.i18n import T_TranslationOrStr, _t


class Hardwood(BaseBonusResource):
    key: str = "resource.core.bonus.hardwood"
    name: T_TranslationOrStr = _t("content.resources.core.hardwood.name")
    description: T_TranslationOrStr = _t("content.resources.core.hardwood.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_hardwood.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 5.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
