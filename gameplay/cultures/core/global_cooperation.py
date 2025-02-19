from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class GlobalCooperation(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.global_cooperation",
            name=_t("content.culture.civics.core.global_cooperation.name"),
            description=_t("content.culture.civics.core.global_cooperation.description"),
            *args,
            **kwargs,
        )
