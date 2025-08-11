from typing import Dict, Type

from gameplay.improvements.core.resources.mine import Mine
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, t_
from gameplay.terrain.hills_desert import HillsDesert
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.terrain.hills_snow import HillsSnow
from gameplay.terrain.hills_tundra import HillsTundra


class Diamonds(BaseLuxuryResource):
    key: str = "resource.core.luxury.diamonds"
    name: T_TranslationOrStr = t_("content.resources.core.diamonds.name")
    description: T_TranslationOrStr = t_("content.resources.core.diamonds.description")
    _color = (1.0, 1.0, 0.0)
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    icon: str = "assets/icons/resources/core/luxury/bordered_diamonds.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        HillsDesert: 50.0,
        HillsGrass: 50.0,
        HillsTundra: 80.0,
        HillsSnow: 80.0,
    }
    spawn_amount = 5.0
    improvement_required = [Mine]

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
