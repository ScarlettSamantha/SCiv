from typing import Dict, Type

from gameplay.improvements.core.resources.fishing_boats import FishingBoats
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.coast import Coast
from gameplay.terrain.lake import Lake
from gameplay.terrain.sea import Sea
from managers.i18n import T_TranslationOrStr, t_


class Pearls(BaseLuxuryResource):
    key: str = "resource.core.luxury.pearls"
    name: T_TranslationOrStr = t_("content.resources.core.pearls.name")
    description: T_TranslationOrStr = t_("content.resources.core.pearls.description")
    _color = (1.0, 1.0, 0.0)
    icon: str = "assets/icons/resources/core/luxury/bordered_pearls.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {BaseTerrain: 0.0, Sea: 20.0, Coast: 90.0, Lake: 50.0}
    coverage = 2.0
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.WATER
    improvement_required = [FishingBoats]

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
