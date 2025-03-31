from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CollectivizedAgriculture(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.collectivized_agriculture",
            name=t_("content.culture.civics.core.collectivized_agriculture.name"),
            description=t_("content.culture.civics.core.collectivized_agriculture.description"),
            *args,
            **kwargs,
        )
