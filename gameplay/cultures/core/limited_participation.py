from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class LimitedParticipation(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.limited_participation",
            name=t_("content.culture.civics.core.limited_participation.name"),
            description=t_("content.culture.civics.core.limited_participation.description"),
            *args,
            **kwargs,
        )
