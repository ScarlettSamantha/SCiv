from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class CulturalExchange(Civic):
    key = "core.culture.civics.cultural_exchange"
    name = t_("content.culture.civics.core.cultural_exchange.name")
    description = t_("content.culture.civics.core.cultural_exchange.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
