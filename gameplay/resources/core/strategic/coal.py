from typing import Tuple
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from managers.i18n import T_TranslationOrStr, _t


class Coal(BaseStrategyResource):
    key: str = "resource.core.strategic.coal"
    name: T_TranslationOrStr = _t("content.resources.core.coal.name")
    description: T_TranslationOrStr = _t("content.resources.core.coal.description")
    spawn_chance: float | Tuple[float, float] = 5.0
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
