from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class MoralLegislation(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.moral_legislation",
            name=t_("content.culture.civics.core.moral_legislation.name"),
            description=t_("content.culture.civics.core.moral_legislation.description"),
            *args,
            **kwargs,
        )
