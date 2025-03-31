from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class UniversalHealthcare(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.universal_healthcare",
            name=t_("content.culture.civics.core.universal_healthcare.name"),
            description=t_("content.culture.civics.core.universal_healthcare.description"),
            *args,
            **kwargs,
        )
