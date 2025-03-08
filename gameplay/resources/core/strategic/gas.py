from typing import Dict, Tuple, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.coast import Coast
from gameplay.terrain.sea import Sea
from managers.i18n import T_TranslationOrStr, _t


class Gas(BaseStrategyResource):
    key: str = "resource.core.strategic.gas"
    name: T_TranslationOrStr = _t("content.resources.core.gas.name")
    description: T_TranslationOrStr = _t("content.resources.core.gas.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {Sea: 15.0, Coast: 5.0, BaseTerrain: 7.0}
    icon: str = "assets/icons/resources/core/strategic/bordered_chemicals.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.BOTH
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
