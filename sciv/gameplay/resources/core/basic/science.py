from typing import Dict, Type

from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, t_


class Science(BasicBaseResource):
    key: str = "resource.core.basic.science"
    name: T_TranslationOrStr = t_("content.resources.science.name")
    description: T_TranslationOrStr = t_("content.resources.science.description")
    icon: str = "assets/icons/default/resources/core/basic/science.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
