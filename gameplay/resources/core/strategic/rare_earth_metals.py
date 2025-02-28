from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from managers.i18n import T_TranslationOrStr, _t


class RareEarthMetals(BaseStrategyResource):
    key: str = "resource.core.strategic.rare_earth_metals"
    name: T_TranslationOrStr = _t("content.resources.core.rare_earth_metals.name")
    description: T_TranslationOrStr = _t("content.resources.core.rare_earth_metals.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 2.0
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
