from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class ReligiousUnity(Civic):
    key = "core.culture.civics.religious_unity"
    name = t_("content.culture.civics.core.religious_unity.name")
    description = t_("content.culture.civics.core.religious_unity.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
