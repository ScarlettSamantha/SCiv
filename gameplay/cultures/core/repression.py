from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class Repression(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.repression",
            name=t_("content.culture.civics.core.repression.name"),
            description=t_("content.culture.civics.core.repression.description"),
            *args,
            **kwargs,
        )
