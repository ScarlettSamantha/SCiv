from typing import Tuple
from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import T_TranslationOrStr, _t


class Culture(BasicBaseResource):
    key: str = "resource.core.basic.culture"
    name: T_TranslationOrStr = _t("content.resources.core.culture.name")
    description: T_TranslationOrStr = _t("content.resources.core.culture.description")
    spawn_chance: float | Tuple[float, float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int = 0):
        super().__init__(value=value)
