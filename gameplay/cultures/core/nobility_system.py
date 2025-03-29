from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class NobilitySystem(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.nobility_system",
            name=t_("content.culture.civics.core.nobility_system.name"),
            description=t_("content.culture.civics.core.nobility_system.description"),
            *args,
            **kwargs,
        )
