from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class Autonomy(Civic):
    key = "core.culture.civics.autonomy"
    name = t_("content.culture.civics.core.autonomy.name")
    description = t_("content.culture.civics.core.autonomy.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
