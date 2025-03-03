from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from data.terrain.coast import Coast
from data.terrain.sea import Sea
from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from managers.i18n import T_TranslationOrStr, _t


class Chemicals(BaseStrategyResource):
    key: str = "resource.core.strategic.chemicals"
    name: T_TranslationOrStr = _t("content.resources.core.chemicals.name")
    description: T_TranslationOrStr = _t("content.resources.core.chemicals.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {Sea: 15.0, Coast: 5.0, BaseTerrain: 7.0}
    icon: str = "assets/icons/resources/core/strategic/bordered_acid.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.BOTH
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
