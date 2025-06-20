from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class SeparationOfPowers(Civic):
    key = "core.culture.civics.separation_of_powers"
    name = t_("content.culture.civics.core.separation_of_powers.name")
    description = t_("content.culture.civics.core.separation_of_powers.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
