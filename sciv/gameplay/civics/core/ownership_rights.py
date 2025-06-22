from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class OwnershipRights(Civic):
    key = "core.culture.civics.ownership_rights"
    name = t_("content.culture.civics.core.ownership_rights.name")
    description = t_("content.culture.civics.core.ownership_rights.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
