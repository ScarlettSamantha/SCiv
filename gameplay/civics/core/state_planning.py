from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class StatePlanning(Civic):
    key = "core.culture.civics.state_planning"
    name = t_("content.culture.civics.core.state_planning.name")
    description = t_("content.culture.civics.core.state_planning.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
