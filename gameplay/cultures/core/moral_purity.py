from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class MoralPurity(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.moral_purity",
            name=t_("content.culture.civics.core.moral_purity.name"),
            description=t_("content.culture.civics.core.moral_purity.description"),
            *args,
            **kwargs,
        )
