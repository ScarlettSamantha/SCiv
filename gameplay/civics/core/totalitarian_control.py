from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class TotalitarianControl(Civic):
    key = "core.culture.civics.totalitarian_control"
    name = t_("content.culture.civics.core.totalitarian_control.name")
    description = t_("content.culture.civics.core.totalitarian_control.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
