from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class SeparationOfPowers(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.separation_of_powers",
            name=t_("content.culture.civics.core.separation_of_powers.name"),
            description=t_("content.culture.civics.core.separation_of_powers.description"),
            *args,
            **kwargs,
        )
