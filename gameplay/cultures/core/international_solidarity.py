from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class InternationalSolidarity(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.international_solidarity",
            name=t_("content.culture.civics.core.international_solidarity.name"),
            description=t_("content.culture.civics.core.international_solidarity.description"),
            *args,
            **kwargs,
        )
