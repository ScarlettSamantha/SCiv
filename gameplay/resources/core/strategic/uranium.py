from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from managers.i18n import T_TranslationOrStr, _t


class Uranium(BaseStrategyResource):
    key: str = "resource.core.strategic.uranium"
    name: T_TranslationOrStr = _t("content.resources.core.uranium.name")
    description: T_TranslationOrStr = _t("content.resources.core.uranium.description")
    icon: str = "assets/icons/resources/core/strategic/bordered_uranium.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 3.0
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
