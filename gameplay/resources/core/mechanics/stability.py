from typing import Tuple
from gameplay.resources.core.mechanics.mechanic_resource import MechanicBaseResource
from managers.i18n import T_TranslationOrStr, _t


class Stability(MechanicBaseResource):
    key: str = "resource.core.mechanic.stability"
    name: T_TranslationOrStr = _t("content.resources.core.stability.name")
    description: T_TranslationOrStr = _t("content.resources.core.stability.description")
    spawn_chance: float | Tuple[float, float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
