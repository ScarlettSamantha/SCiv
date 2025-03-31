from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class Autonomy(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.autonomy",
            name=t_("content.culture.civics.core.autonomy.name"),
            description=t_("content.culture.civics.core.autonomy.description"),
            *args,
            **kwargs,
        )
