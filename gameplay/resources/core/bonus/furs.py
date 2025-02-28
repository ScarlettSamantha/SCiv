from typing import Dict, Tuple
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from managers.i18n import T_TranslationOrStr, _t


class Furs(BaseBonusResource):
    key: str = "resource.core.bonus.furs"
    name: T_TranslationOrStr = _t("content.resources.core.furs.name")
    description: T_TranslationOrStr = _t("content.resources.core.furs.description")
    spawn_chance: float | Dict[BaseTerrain, float] = 5.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
