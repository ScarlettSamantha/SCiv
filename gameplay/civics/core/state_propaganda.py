from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class StatePropaganda(Civic):
    key = "core.culture.civics.state_propaganda"
    name = t_("content.culture.civics.core.state_propaganda.name")
    description = t_("content.culture.civics.core.state_propaganda.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
