from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class CorporateState(Civic):
    key = "core.culture.civics.corporate_state"
    name = t_("content.culture.civics.core.corporate_state.name")
    description = t_("content.culture.civics.core.corporate_state.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
