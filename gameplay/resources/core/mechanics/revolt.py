from typing import Dict, Tuple, Type

from gameplay.resources.core.mechanics.mechanic_resource import MechanicBaseResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Revolt(MechanicBaseResource):
    key: str = "resource.core.mechanic.revolt"
    name: T_TranslationOrStr = _t("content.resources.core.revolt.name")
    description: T_TranslationOrStr = _t("content.resources.core.revolt.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
