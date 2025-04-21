from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Decentralization(Civic):
    key = "core.culture.civics.decentralization"
    name = t_("content.culture.civics.core.decentralization.name")
    description = t_("content.culture.civics.core.decentralization.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
