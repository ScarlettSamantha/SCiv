from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class ScientificRevolution(Civic):
    key = "core.culture.civics.scientific_revolution"
    name = t_("content.culture.civics.core.scientific_revolution.name")
    description = t_("content.culture.civics.core.scientific_revolution.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
