from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class RareEarthMetals(BaseStrategicResource):
    key: str = "resource.core.strategic.rare_earth_metals"
    name: T_TranslationOrStr = _t("content.resources.core.rare_earth_metals.name")
    description: T_TranslationOrStr = _t("content.resources.core.rare_earth_metals.description")
    _color = (1.0, 0.0, 0.0)
    icon: str = "assets/icons/resources/core/strategic/bordered_rare_earth_metals.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 100
    spawn_amount = 3.0
    coverage = 0.5

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
