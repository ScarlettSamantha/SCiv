from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class RoyalPatronage(Civic):
    key = "core.culture.civics.royal_patronage"
    name = t_("content.culture.civics.core.royal_patronage.name")
    description = t_("content.culture.civics.core.royal_patronage.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
