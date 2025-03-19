from typing import Dict, Tuple, Type

from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Aluminium(BaseStrategyResource):
    key: str = "resource.core.strategic.aluminium"
    name: T_TranslationOrStr = _t("content.resources.core.aluminium.name")
    description: T_TranslationOrStr = _t("content.resources.core.aluminium.description")
    icon: str = "assets/icons/resources/core/strategic/bordered_rare_earth_rods.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 15.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
