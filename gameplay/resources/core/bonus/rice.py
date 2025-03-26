from typing import Dict, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_grass import HillsGrass
from managers.i18n import T_TranslationOrStr, _t


class Rice(BaseBonusResource):
    key: str = "resource.core.bonus.rice"
    name: T_TranslationOrStr = _t("content.resources.core.rice.name")
    description: T_TranslationOrStr = _t("content.resources.core.rice.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_rice.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatGrass: 100.0,
        FlatForest: 40.0,
        HillsForest: 40.0,
        HillsGrass: 50.0,
    }
    coverage = 1.3
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
