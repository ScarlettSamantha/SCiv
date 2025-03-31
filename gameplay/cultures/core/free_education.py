from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class FreeEducation(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.free_education",
            name=t_("content.culture.civics.core.free_education.name"),
            description=t_("content.culture.civics.core.free_education.description"),
            *args,
            **kwargs,
        )
