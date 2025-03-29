from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class SimplifiedLiving(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.simplified_living",
            name=t_("content.culture.civics.core.simplified_living.name"),
            description=t_("content.culture.civics.core.simplified_living.description"),
            *args,
            **kwargs,
        )
