from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class FeudalObligations(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.feudal_obligations",
            name=t_("content.culture.civics.core.feudal_obligations.name"),
            description=t_("content.culture.civics.core.feudal_obligations.description"),
            *args,
            **kwargs,
        )
