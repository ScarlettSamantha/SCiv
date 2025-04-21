from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class VoluntaryAssociations(Civic):
    key = "core.culture.civics.voluntary_associations"
    name = t_("content.culture.civics.core.voluntary_associations.name")
    description = t_("content.culture.civics.core.voluntary_associations.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
