from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Propaganda(Civic):
    key = "core.culture.civics.propaganda"
    name = t_("content.culture.civics.core.propaganda.name")
    description = t_("content.culture.civics.core.propaganda.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
