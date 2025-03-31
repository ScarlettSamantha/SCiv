from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CentralizedEconomy(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.centralized_economy",
            name=t_("content.culture.civics.core.centralized_economy.name"),
            description=t_("content.culture.civics.core.centralized_economy.description"),
            *args,
            **kwargs,
        )
