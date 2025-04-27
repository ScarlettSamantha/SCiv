from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class MoralLegislation(Civic):
    key = "core.culture.civics.moral_legislation"
    name = t_("content.culture.civics.core.moral_legislation.name")
    description = t_("content.culture.civics.core.moral_legislation.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
