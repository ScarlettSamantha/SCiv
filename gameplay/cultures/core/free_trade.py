from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class FreeTrade(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.free_trade",
            name=_t("content.culture.civics.core.free_trade.name"),
            description=_t("content.culture.civics.core.free_trade.description"),
            *args,
            **kwargs,
        )
