from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ProletarianDictatorship(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.proletarian_dictatorship",
            name=t_("content.culture.civics.core.proletarian_dictatorship.name"),
            description=t_("content.culture.civics.core.proletarian_dictatorship.description"),
            *args,
            **kwargs,
        )
