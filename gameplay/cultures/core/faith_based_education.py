from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class FaithBasedEducation(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.faith_based_education",
            name=t_("content.culture.civics.core.faith_based_education.name"),
            description=t_("content.culture.civics.core.faith_based_education.description"),
            *args,
            **kwargs,
        )
