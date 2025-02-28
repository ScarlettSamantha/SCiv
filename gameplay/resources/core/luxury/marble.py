from typing import Dict, Tuple
from data.terrain._base_terrain import BaseTerrain
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from managers.i18n import T_TranslationOrStr, _t


class Marble(BaseLuxuryResource):
    key: str = "resource.core.luxury.marble"
    name: T_TranslationOrStr = _t("content.resources.core.marble.name")
    description: T_TranslationOrStr = _t("content.resources.core.marble.description")
    spawn_chance: float | Dict[BaseTerrain, float] = 15.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
