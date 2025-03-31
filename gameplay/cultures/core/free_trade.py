from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class FreeTrade(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.free_trade",
            name=t_("content.culture.civics.core.free_trade.name"),
            description=t_("content.culture.civics.core.free_trade.description"),
            *args,
            **kwargs,
        )
