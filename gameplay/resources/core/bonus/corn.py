from typing import Dict, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.tiles.land_grass import FlatGrass
from managers.i18n import T_TranslationOrStr, _t


class Corn(BaseBonusResource):
    key: str = "resource.core.bonus.corn"
    name: T_TranslationOrStr = _t("content.resources.core.corn.name")
    description: T_TranslationOrStr = _t("content.resources.core.corn.description")
    icon: str = "assets/icons/resources/core/bonus/bordered_corn.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        FlatGrass: 100.0,
        HillsGrass: 100.0,
        BaseTerrain: 0.0,
    }
    spawn_amount = 5.0
    coverage = 0.4

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
