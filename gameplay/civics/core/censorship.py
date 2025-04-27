from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Censorship(Civic):
    key = "core.culture.civics.censorship"
    name = t_("content.culture.civics.core.censorship.name")
    description = t_("content.culture.civics.core.censorship.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
