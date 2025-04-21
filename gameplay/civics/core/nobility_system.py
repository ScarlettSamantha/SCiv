from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class NobilitySystem(Civic):
    key = "core.culture.civics.nobility_system"
    name = t_("content.culture.civics.core.nobility_system.name")
    description = t_("content.culture.civics.core.nobility_system.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
