from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Meritocracy(Civic):
    key = "core.culture.civics.meritocracy"
    name = t_("content.culture.civics.core.meritocracy.name")
    description = t_("content.culture.civics.core.meritocracy.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
