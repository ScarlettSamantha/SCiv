from typing import Dict, Tuple, Type
from data.terrain._base_terrain import BaseTerrain
from data.terrain.flat_grass import FlatGrass
from data.terrain.hills_grass import HillsGrass
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from managers.i18n import T_TranslationOrStr, _t


class Wheat(BaseBonusResource):
    key: str = "resource.core.bonus.wheat"
    name: T_TranslationOrStr = _t("content.resources.core.wheat.name")
    description: T_TranslationOrStr = _t("content.resources.core.wheat.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {FlatGrass: 10, HillsGrass: 5, BaseTerrain: 1}
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
