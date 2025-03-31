from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class EconomicIntegration(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.economic_integration",
            name=t_("content.culture.civics.core.economic_integration.name"),
            description=t_("content.culture.civics.core.economic_integration.description"),
            *args,
            **kwargs,
        )
