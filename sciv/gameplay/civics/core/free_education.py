from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class FreeEducation(Civic):
    key = "core.culture.civics.free_education"
    name = t_("content.culture.civics.core.free_education.name")
    description = t_("content.culture.civics.core.free_education.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
