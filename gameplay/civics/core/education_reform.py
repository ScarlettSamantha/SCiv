from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class EducationReform(Civic):
    key = "core.culture.civics.education_reform"
    name = t_("content.culture.civics.core.education_reform.name")
    description = t_("content.culture.civics.core.education_reform.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
