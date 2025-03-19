from typing import Dict, Tuple, Type

from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Faith(BasicBaseResource):
    key: str = "resource.core.basic.faith"
    name: T_TranslationOrStr = _t("content.resources.core.faith.name")
    description: T_TranslationOrStr = _t("content.resources.core.faith.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
