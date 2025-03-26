from typing import Dict, Type

from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_desert import FlatDessert
from gameplay.terrain.flat_savanna import FlatSavanna
from managers.i18n import T_TranslationOrStr, _t


class Ivory(BaseLuxuryResource):
    key: str = "resource.core.luxury.ivory"
    name: T_TranslationOrStr = _t("content.resources.core.ivory.name")
    description: T_TranslationOrStr = _t("content.resources.core.ivory.description")
    icon: str = "assets/icons/resources/core/luxury/hex_border_ivory.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatSavanna: 70.0,
        FlatDessert: 70.0,
    }
    coverage = 0.3
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
