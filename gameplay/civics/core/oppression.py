from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Oppression(Civic):
    key = "core.culture.civics.oppression"
    name = t_("content.culture.civics.core.oppression.name")
    description = t_("content.culture.civics.core.oppression.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
