from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Entrepreneurship(Civic):
    key = "core.culture.civics.entrepreneurship"
    name = t_("content.culture.civics.core.entrepreneurship.name")
    description = t_("content.culture.civics.core.entrepreneurship.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
