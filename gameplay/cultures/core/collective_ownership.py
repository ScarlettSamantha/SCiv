from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CollectiveOwnership(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.collective_ownership",
            name=t_("content.culture.civics.core.collective_ownership.name"),
            description=t_("content.culture.civics.core.collective_ownership.description"),
            *args,
            **kwargs,
        )
