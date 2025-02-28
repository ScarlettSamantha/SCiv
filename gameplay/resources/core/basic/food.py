from typing import Dict, Tuple
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import T_TranslationOrStr, _t


class Food(BasicBaseResource):
    key: str = "resource.core.basic.food"
    name: T_TranslationOrStr = _t("content.resources.core.food.name")
    description: T_TranslationOrStr = _t("content.resources.core.food.description")
    spawn_chance: float | Dict[BaseTerrain, float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
