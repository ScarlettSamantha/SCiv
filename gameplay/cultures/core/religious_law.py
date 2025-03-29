from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ReligiousLaw(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.religious_law",
            name=t_("content.culture.civics.core.religious_law.name"),
            description=t_("content.culture.civics.core.religious_law.description"),
            *args,
            **kwargs,
        )
