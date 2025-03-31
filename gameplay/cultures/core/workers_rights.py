from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class WorkersRights(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.workers_rights",
            name=t_("content.culture.civics.core.workers_rights.name"),
            description=t_("content.culture.civics.core.workers_rights.description"),
            *args,
            **kwargs,
        )
