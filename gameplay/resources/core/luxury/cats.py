from typing import Tuple
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from managers.i18n import T_TranslationOrStr, _t


class Cats(BaseLuxuryResource):
    name: T_TranslationOrStr = _t("content.resources.core.cats.name")
    description: T_TranslationOrStr = _t("content.resources.core.cats.description")
    spawn_chance: float | Tuple[float, float] = 5.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__("resource.core.strategic.cats", value=value)
