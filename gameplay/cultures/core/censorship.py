from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class Censorship(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.censorship",
            name=t_("content.culture.civics.core.censorship.name"),
            description=t_("content.culture.civics.core.censorship.description"),
            *args,
            **kwargs,
        )
