from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class ScientificManagement(Civic):
    key = "core.culture.civics.scientific_management"
    name = t_("content.culture.civics.core.scientific_management.name")
    description = t_("content.culture.civics.core.scientific_management.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
