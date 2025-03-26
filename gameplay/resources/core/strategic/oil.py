from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.coast import Coast
from gameplay.terrain.flat_desert import FlatDessert
from gameplay.terrain.flat_savanna import FlatSavanna
from gameplay.terrain.sea import Sea
from managers.i18n import T_TranslationOrStr, _t


class Oil(BaseStrategicResource):
    key: str = "resource.core.strategic.oil"
    name: T_TranslationOrStr = _t("content.resources.core.oil.name")
    description: T_TranslationOrStr = _t("content.resources.core.oil.description")
    _color = (1.0, 0.0, 0.0)
    coverage = 3
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        Sea: 70.0,
        Coast: 40.0,
        BaseTerrain: 0.0,
        FlatSavanna: 70.0,
        FlatDessert: 70.0,
    }
    icon: str = "assets/icons/resources/core/strategic/bordered_oil.png"
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.BOTH
    spawn_amount = 3.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
