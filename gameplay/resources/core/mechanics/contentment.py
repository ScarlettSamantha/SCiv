from typing import Tuple
from gameplay.resources.core.mechanics.mechanic_resource import MechanicBaseResource
from managers.i18n import T_TranslationOrStr, _t


class Contentment(MechanicBaseResource):
    name: T_TranslationOrStr = _t("content.resources.core.contentment.name")
    description: T_TranslationOrStr = _t("content.resources.core.contentment.description")
    spawn_chance: float | Tuple[float, float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int = 0):
        super().__init__("resource.core.mechanic.contentment", value=value)
