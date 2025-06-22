from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class SimplifiedLiving(Civic):
    key = "core.culture.civics.simplified_living"
    name = t_("content.culture.civics.core.simplified_living.name")
    description = t_("content.culture.civics.core.simplified_living.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
