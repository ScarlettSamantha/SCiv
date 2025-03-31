from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class VoluntaryAssociations(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.voluntary_associations",
            name=t_("content.culture.civics.core.voluntary_associations.name"),
            description=t_("content.culture.civics.core.voluntary_associations.description"),
            *args,
            **kwargs,
        )
