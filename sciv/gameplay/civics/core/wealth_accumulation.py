from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class WealthAccumulation(Civic):
    key = "core.culture.civics.wealth_accumulation"
    name = t_("content.culture.civics.core.wealth_accumulation.name")
    description = t_("content.culture.civics.core.wealth_accumulation.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
