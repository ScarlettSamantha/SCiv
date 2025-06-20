from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class ElectoralProcess(Civic):
    key = "core.culture.civics.electoral_process"
    name = t_("content.culture.civics.core.electoral_process.name")
    description = t_("content.culture.civics.core.electoral_process.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
