from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class MoralPolicing(Civic):
    key = "core.culture.civics.moral_policing"
    name = t_("content.culture.civics.core.moral_policing.name")
    description = t_("content.culture.civics.core.moral_policing.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
