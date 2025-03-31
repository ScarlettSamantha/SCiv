from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class NationalPurity(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.national_purity",
            name=t_("content.culture.civics.core.national_purity.name"),
            description=t_("content.culture.civics.core.national_purity.description"),
            *args,
            **kwargs,
        )
