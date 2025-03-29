from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CollectiveSecurity(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.collective_security",
            name=t_("content.culture.civics.core.collective_security.name"),
            description=t_("content.culture.civics.core.collective_security.description"),
            *args,
            **kwargs,
        )
