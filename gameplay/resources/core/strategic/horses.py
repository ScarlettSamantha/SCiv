from typing import Tuple
from gameplay.resources.core.strategic.strategic_resource import BaseStrategyResource
from managers.i18n import T_TranslationOrStr, _t


class Horses(BaseStrategyResource):
    name: T_TranslationOrStr = _t("content.resources.core.horses.name")
    description: T_TranslationOrStr = _t("content.resources.core.horses.description")
    spawn_chance: float | Tuple[float, float] = 10.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__("resource.core.strategic.horses", value=value)
