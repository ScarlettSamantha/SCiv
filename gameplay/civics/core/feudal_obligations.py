from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class FeudalObligations(Civic):
    key = "core.culture.civics.feudal_obligations"
    name = t_("content.culture.civics.core.feudal_obligations.name")
    description = t_("content.culture.civics.core.feudal_obligations.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
