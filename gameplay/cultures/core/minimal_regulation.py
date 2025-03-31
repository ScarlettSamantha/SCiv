from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class MinimalRegulation(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.minimal_regulation",
            name=t_("content.culture.civics.core.minimal_regulation.name"),
            description=t_("content.culture.civics.core.minimal_regulation.description"),
            *args,
            **kwargs,
        )
