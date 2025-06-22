from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class PatrioticEducation(Civic):
    key = "core.culture.civics.patriotic_education"
    name = t_("content.culture.civics.core.patriotic_education.name")
    description = t_("content.culture.civics.core.patriotic_education.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
