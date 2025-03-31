from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ScientificManagement(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.scientific_management",
            name=t_("content.culture.civics.core.scientific_management.name"),
            description=t_("content.culture.civics.core.scientific_management.description"),
            *args,
            **kwargs,
        )
