from typing import Dict, Tuple, Type

from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import T_TranslationOrStr, _t


class Culture(BasicBaseResource):
    from gameplay.terrain._base_terrain import BaseTerrain

    key: str = "resource.core.basic.culture"
    name: T_TranslationOrStr = _t("content.resources.core.culture.name")
    description: T_TranslationOrStr = _t("content.resources.core.culture.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0
    spawn_amount: float | Tuple[float, float] = 0
    icon: str = "assets/icons/resources/core/basic/culture.png"

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
