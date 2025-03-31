from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ReligiousDiscipline(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.religious_discipline",
            name=t_("content.culture.civics.core.religious_discipline.name"),
            description=t_("content.culture.civics.core.religious_discipline.description"),
            *args,
            **kwargs,
        )
