from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class DirectAction(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.direct_action",
            name=t_("content.culture.civics.core.direct_action.name"),
            description=t_("content.culture.civics.core.direct_action.description"),
            *args,
            **kwargs,
        )
