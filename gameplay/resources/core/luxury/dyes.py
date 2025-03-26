from typing import Dict, Type

from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_jungle import FlatJungle
from gameplay.terrain.flat_light_jungle import FlatLightJungle
from managers.i18n import T_TranslationOrStr, _t


class Dyes(BaseLuxuryResource):
    key: str = "resource.core.luxury.dyes"
    name: T_TranslationOrStr = _t("content.resources.core.dyes.name")
    description: T_TranslationOrStr = _t("content.resources.core.dyes.description")
    icon: str = "assets/icons/resources/core/luxury/hex_border_dyes.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatJungle: 70.0,
        FlatLightJungle: 70.0,
    }
    spawn_amount = 5.0
    coverage = 0.2

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
