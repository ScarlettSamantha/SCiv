from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ReligiousUnity(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.religious_unity",
            name=t_("content.culture.civics.core.religious_unity.name"),
            description=t_("content.culture.civics.core.religious_unity.description"),
            *args,
            **kwargs,
        )
