from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class EconomicFocus(Civic):
    key = "core.culture.civics.economic_focus"
    name = t_("content.culture.civics.core.economic_focus.name")
    description = t_("content.culture.civics.core.economic_focus.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
