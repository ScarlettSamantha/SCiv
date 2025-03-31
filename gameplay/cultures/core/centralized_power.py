from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CentralizedPower(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.centralized_power",
            name=t_("content.culture.civics.core.centralized_power.name"),
            description=t_("content.culture.civics.core.centralized_power.description"),
            *args,
            **kwargs,
        )
