from typing import Tuple
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from managers.i18n import T_TranslationOrStr, _t


class Cows(BaseBonusResource):
    name: T_TranslationOrStr = _t("content.resources.core.cows.name")
    description: T_TranslationOrStr = _t("content.resources.core.cows.description")
    spawn_chance: float | Tuple[float, float] = 5.0
    spawn_amount: float | Tuple[float, float] = 5.0

    def __init__(self, value: int = 0):
        super().__init__("resource.core.strategic.cows", value=value)
