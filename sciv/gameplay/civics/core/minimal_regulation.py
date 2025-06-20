from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class MinimalRegulation(Civic):
    key = "core.culture.civics.minimal_regulation"
    name = t_("content.culture.civics.core.minimal_regulation.name")
    description = t_("content.culture.civics.core.minimal_regulation.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
