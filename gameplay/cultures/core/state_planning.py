from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class StatePlanning(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.state_planning",
            name=t_("content.culture.civics.core.state_planning.name"),
            description=t_("content.culture.civics.core.state_planning.description"),
            *args,
            **kwargs,
        )
