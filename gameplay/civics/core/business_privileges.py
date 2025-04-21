from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class BusinessPrivileges(Civic):
    key = "core.culture.civics.business_privileges"
    name = t_("content.culture.civics.core.business_privileges.name")
    description = t_("content.culture.civics.core.business_privileges.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
