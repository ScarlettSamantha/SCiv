from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Repression(Civic):
    key = "core.culture.civics.repression"
    name = t_("content.culture.civics.core.repression.name")
    description = t_("content.culture.civics.core.repression.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
