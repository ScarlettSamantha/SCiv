from typing import Dict, Tuple, Type

from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Horses(BaseStrategyResource):
    key: str = "resource.core.strategic.horses"
    name: T_TranslationOrStr = _t("content.resources.core.horses.name")
    description: T_TranslationOrStr = _t("content.resources.core.horses.description")
    icon: str = "assets/icons/resources/core/strategic/bordered_horse.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 30.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
