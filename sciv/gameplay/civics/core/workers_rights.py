from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class WorkersRights(Civic):
    key = "core.culture.civics.workers_rights"
    name = t_("content.culture.civics.core.workers_rights.name")
    description = t_("content.culture.civics.core.workers_rights.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
