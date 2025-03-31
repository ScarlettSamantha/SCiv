from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class NationalSovereignty(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.national_sovereignty",
            name=t_("content.culture.civics.core.national_sovereignty.name"),
            description=t_("content.culture.civics.core.national_sovereignty.description"),
            *args,
            **kwargs,
        )
