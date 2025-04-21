from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class MilitaryStrength(Civic):
    key = "core.culture.civics.military_strength"
    name = t_("content.culture.civics.core.military_strength.name")
    description = t_("content.culture.civics.core.military_strength.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
