from typing import Dict, Tuple
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from managers.i18n import T_TranslationOrStr, _t


class Gas(BaseStrategyResource):
    key: str = "resource.core.strategic.gas"
    name: T_TranslationOrStr = _t("content.resources.core.gas.name")
    description: T_TranslationOrStr = _t("content.resources.core.gas.description")
    spawn_chance: float | Dict[BaseTerrain, float] = 15.0
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
