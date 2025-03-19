from typing import Dict, Tuple, Type

from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Coal(BaseStrategyResource):
    key: str = "resource.core.strategic.coal"
    name: T_TranslationOrStr = _t("content.resources.core.coal.name")
    description: T_TranslationOrStr = _t("content.resources.core.coal.description")
    icon: str = "assets/icons/resources/core/strategic/bordered_coal.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 15.0
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
