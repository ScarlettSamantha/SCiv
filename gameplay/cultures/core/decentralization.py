from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class Decentralization(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.decentralization",
            name=t_("content.culture.civics.core.decentralization.name"),
            description=t_("content.culture.civics.core.decentralization.description"),
            *args,
            **kwargs,
        )
