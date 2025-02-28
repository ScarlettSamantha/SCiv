from typing import Tuple
from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import T_TranslationOrStr, _t


class Production(BasicBaseResource):
    name: T_TranslationOrStr = _t("content.resources.core.production.name")
    description: T_TranslationOrStr = _t("content.resources.core.production.description")
    spawn_chance: float | Tuple[float, float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int = 0):
        super().__init__("resource.core.strategic.production", value=value)
