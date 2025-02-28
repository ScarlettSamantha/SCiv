from typing import Dict, Tuple
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.resource import ResourceSpawnablePlace
from data.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Fish(BaseBonusResource):
    key: str = "resource.core.bonus.fish"
    name: T_TranslationOrStr = _t("content.resources.core.fish.name")
    description: T_TranslationOrStr = _t("content.resources.core.fish.description")
    spawn_chance: float | Dict[BaseTerrain, float] = 25.0
    spawn_amount: float | Tuple[float, float] = 3.0
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.WATER

    def __init__(self, value: int = 0):
        super().__init__(value=value)
