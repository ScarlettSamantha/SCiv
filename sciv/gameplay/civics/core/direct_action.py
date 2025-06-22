from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class DirectAction(Civic):
    key = "core.culture.civics.direct_action"
    name = t_("content.culture.civics.core.direct_action.name")
    description = t_("content.culture.civics.core.direct_action.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
