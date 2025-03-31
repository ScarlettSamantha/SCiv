from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class EducationReform(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.education_reform",
            name=t_("content.culture.civics.core.education_reform.name"),
            description=t_("content.culture.civics.core.education_reform.description"),
            *args,
            **kwargs,
        )
