from typing import Dict, Type

from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Production(BasicBaseResource):
    key: str = "resource.core.basic.production"
    name: T_TranslationOrStr = _t("content.resources.core.production.name")
    description: T_TranslationOrStr = _t("content.resources.core.production.description")
    icon: str = "assets/icons/resources/core/basic/production.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
