from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.coast import Coast
from gameplay.terrain.sea import Sea
from gameplay.terrain.sea_ice import SeaIce
from managers.i18n import T_TranslationOrStr, t_


class Gas(BaseStrategicResource):
    key: str = "resource.core.strategic.gas"
    name: T_TranslationOrStr = t_("content.resources.core.gas.name")
    description: T_TranslationOrStr = t_("content.resources.core.gas.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {Sea: 70.0, Coast: 30.0, BaseTerrain: 40.0, SeaIce: 90.0}
    _color = (1.0, 0.0, 0.0)
    icon: str = "assets/icons/default/resources/core/strategic/bordered_chemicals.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.BOTH
    spawn_amount = 3.0
    coverage = 0.8

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
