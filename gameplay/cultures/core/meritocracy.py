from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class Meritocracy(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.meritocracy",
            name=t_("content.culture.civics.core.meritocracy.name"),
            description=t_("content.culture.civics.core.meritocracy.description"),
            *args,
            **kwargs,
        )
