from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from managers.i18n import T_TranslationOrStr, _t


class Potato(BaseBonusResource):
    key: str = "resource.core.bonus.potato"
    name: T_TranslationOrStr = _t("content.resources.core.potato.name")
    description: T_TranslationOrStr = _t("content.resources.core.potato.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 6.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
