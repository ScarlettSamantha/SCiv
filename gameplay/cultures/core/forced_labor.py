from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ForcedLabor(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.forced_labor",
            name=t_("content.culture.civics.core.forced_labor.name"),
            description=t_("content.culture.civics.core.forced_labor.description"),
            *args,
            **kwargs,
        )
