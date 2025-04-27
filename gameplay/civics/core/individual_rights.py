from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class IndividualRights(Civic):
    key = "core.culture.civics.individual_rights"
    name = t_("content.culture.civics.core.individual_rights.name")
    description = t_("content.culture.civics.core.individual_rights.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
