from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class StatePropaganda(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.state_propaganda",
            name=t_("content.culture.civics.core.state_propaganda.name"),
            description=t_("content.culture.civics.core.state_propaganda.description"),
            *args,
            **kwargs,
        )
