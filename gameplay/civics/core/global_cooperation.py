from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class GlobalCooperation(Civic):
    key = "core.culture.civics.global_cooperation"
    name = t_("content.culture.civics.core.global_cooperation.name")
    description = t_("content.culture.civics.core.global_cooperation.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
