from typing import Tuple
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from managers.i18n import T_TranslationOrStr, _t


class Gas(BaseStrategyResource):
    name: T_TranslationOrStr = _t("content.resources.core.gas.name")
    description: T_TranslationOrStr = _t("content.resources.core.gas.description")
    spawn_chance: float | Tuple[float, float] = 5.0
    spawn_amount: float | Tuple[float, float] = 3.0

    def __init__(self, value: int = 0):
        super().__init__("resource.core.strategic.gas", value=value)
