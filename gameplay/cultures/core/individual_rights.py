from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class IndividualRights(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.individual_rights",
            name=t_("content.culture.civics.core.individual_rights.name"),
            description=t_("content.culture.civics.core.individual_rights.description"),
            *args,
            **kwargs,
        )
