from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class RoyalPatronage(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.royal_patronage",
            name=t_("content.culture.civics.core.royal_patronage.name"),
            description=t_("content.culture.civics.core.royal_patronage.description"),
            *args,
            **kwargs,
        )
