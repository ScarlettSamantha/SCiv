from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class CulturalPreservation(Civic):
    key = "core.culture.civics.cultural_preservation"
    name = t_("content.culture.civics.core.cultural_preservation.name")
    description = t_("content.culture.civics.core.cultural_preservation.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
