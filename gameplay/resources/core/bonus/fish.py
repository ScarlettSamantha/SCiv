from typing import Dict, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.coast import Coast
from gameplay.terrain.sea import Sea
from gameplay.terrain.sea_ice import SeaIce
from gameplay.yields import Yields
from managers.i18n import T_TranslationOrStr, _t


class Fish(BaseBonusResource):
    key: str = "resource.core.bonus.fish"
    name: T_TranslationOrStr = _t("content.resources.core.fish.name")
    _color = (1.0, 0.0, 1.0)
    description: T_TranslationOrStr = _t("content.resources.core.fish.description")
    icon: str = "assets/icons/resources/core/bonus/bordered_fish.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {Sea: 50.0, Coast: 90.0, SeaIce: 0.0}
    spawn_amount = 5.0
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.WATER
    coverage = 4.5
    clusterable = True
    cluster_max_radius = 3
    cluster_dropoff_amount_rate = 1.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
        self.add_to_yield_modifier(Yields(food=2))
