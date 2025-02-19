from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class EconomicControl(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.economic_control",
            name=_t("content.culture.civics.core.economic_control.name"),
            description=_t("content.culture.civics.core.economic_control.description"),
            *args,
            **kwargs,
        )
