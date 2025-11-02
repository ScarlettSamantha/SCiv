from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.deer import HuntingCamp
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_forest import FlatForest
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.flat_tundra import FlatTundra
from gameplay.terrain.hills_forest import HillsForest
from gameplay.terrain.hills_tundra import HillsTundra
from managers.i18n import T_TranslationOrStr, t_


class Furs(BaseLuxuryResource):
    key: str = "resource.core.luxury.furs"
    name: T_TranslationOrStr = t_("content.resources.core.furs.name")
    description: T_TranslationOrStr = t_("content.resources.core.furs.description")
    _color = (1.0, 1.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/default/resources/core/luxury/hex_border_furs.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatScrubland: 70.0,
        FlatForest: 50.0,
        HillsForest: 30.0,
        HillsTundra: 40.0,
        FlatTundra: 20.0,
    }
    spawn_amount = 5.0
    improvement_required = [HuntingCamp]

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
