from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class CollectivizedAgriculture(Civic):
    key = "core.culture.civics.collectivized_agriculture"
    name = t_("content.culture.civics.core.collectivized_agriculture.name")
    description = t_("content.culture.civics.core.collectivized_agriculture.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
