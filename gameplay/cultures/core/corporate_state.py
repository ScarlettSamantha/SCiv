from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CorporateState(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.corporate_state",
            name=t_("content.culture.civics.core.corporate_state.name"),
            description=t_("content.culture.civics.core.corporate_state.description"),
            *args,
            **kwargs,
        )
