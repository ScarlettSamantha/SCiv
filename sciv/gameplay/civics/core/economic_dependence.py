from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class EconomicDependence(Civic):
    key = "core.culture.civics.economic_dependence"
    name = t_("content.culture.civics.core.economic_dependence.name")
    description = t_("content.culture.civics.core.economic_dependence.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
