from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class MilitaryStrength(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.military_strength",
            name=t_("content.culture.civics.core.military_strength.name"),
            description=t_("content.culture.civics.core.military_strength.description"),
            *args,
            **kwargs,
        )
