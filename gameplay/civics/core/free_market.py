from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class FreeMarket(Civic):
    key = "core.culture.civics.free_market"
    name = t_("content.culture.civics.core.free_market.name")
    description = t_("content.culture.civics.core.free_market.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
