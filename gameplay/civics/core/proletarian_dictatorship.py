from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class ProletarianDictatorship(Civic):
    key = "core.culture.civics.proletarian_dictatorship"
    name = t_("content.culture.civics.core.proletarian_dictatorship.name")
    description = t_("content.culture.civics.core.proletarian_dictatorship.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
