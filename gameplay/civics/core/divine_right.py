from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class DivineRight(Civic):
    key = "core.culture.civics.divine_right"
    name = t_("content.culture.civics.core.divine_right.name")
    description = t_("content.culture.civics.core.divine_right.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
