from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_heavy_forest import FlatHeavyForest
from gameplay.terrain.flat_scrubland import FlatScrubland
from managers.i18n import T_TranslationOrStr, _t


class Pigs(BaseBonusResource):
    key: str = "resource.core.bonus.pigs"
    name: T_TranslationOrStr = _t("content.resources.core.pigs.name")
    description: T_TranslationOrStr = _t("content.resources.core.pigs.description")
    _color = (1.0, 0.0, 1.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/bonus/hex_border_pigs.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatForest: 40.0,
        FlatGrass: 30.0,
        FlatHeavyForest: 40.0,
        FlatScrubland: 80.0,
    }
    spawn_amount = 5.0
    coverage = 0.7

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
