from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class Oppression(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.oppression",
            name=t_("content.culture.civics.core.oppression.name"),
            description=t_("content.culture.civics.core.oppression.description"),
            *args,
            **kwargs,
        )
