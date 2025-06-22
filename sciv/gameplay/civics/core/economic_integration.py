from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class EconomicIntegration(Civic):
    key = "core.culture.civics.economic_integration"
    name = t_("content.culture.civics.core.economic_integration.name")
    description = t_("content.culture.civics.core.economic_integration.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
