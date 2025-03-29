from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ReasonAndLogic(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.reason_and_logic",
            name=t_("content.culture.civics.core.reason_and_logic.name"),
            description=t_("content.culture.civics.core.reason_and_logic.description"),
            *args,
            **kwargs,
        )
