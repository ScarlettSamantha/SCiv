from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class DivineRight(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.divine_right",
            name=t_("content.culture.civics.core.divine_right.name"),
            description=t_("content.culture.civics.core.divine_right.description"),
            *args,
            **kwargs,
        )
