from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class MutualAid(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.mutual_aid",
            name=t_("content.culture.civics.core.mutual_aid.name"),
            description=t_("content.culture.civics.core.mutual_aid.description"),
            *args,
            **kwargs,
        )
