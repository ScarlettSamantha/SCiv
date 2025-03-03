from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import T_TranslationOrStr, _t


class Gold(BasicBaseResource):
    key: str = "resource.core.basic.gold"
    name: T_TranslationOrStr = _t("content.resources.core.gold.name")
    description: T_TranslationOrStr = _t("content.resources.core.gold.description")
    icon: str = "assets/icons/resources/core/basic/gold.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int | float = 0):
        
        super().__init__(value=value)
