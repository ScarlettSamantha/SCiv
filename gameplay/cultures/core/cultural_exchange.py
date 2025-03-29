from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CulturalExchange(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.cultural_exchange",
            name=t_("content.culture.civics.core.cultural_exchange.name"),
            description=t_("content.culture.civics.core.cultural_exchange.description"),
            *args,
            **kwargs,
        )
