from typing import Dict, Tuple, Type

from gameplay.resource import ResourceSpawnablePlace
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.coast import Coast
from gameplay.terrain.sea import Sea
from managers.i18n import T_TranslationOrStr, _t


class Clams(BaseBonusResource):
    key: str = "resource.core.bonus.clams"
    name: T_TranslationOrStr = _t("content.resources.core.clams.name")
    description: T_TranslationOrStr = _t("content.resources.core.clams.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        Sea: 10.0,
        Coast: 15.0,
    }
    spawn_amount: float | Tuple[float, float] = 3.0
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.WATER

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
