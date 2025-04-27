from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class SharedSovereignty(Civic):
    key = "core.culture.civics.shared_sovereignty"
    name = t_("content.culture.civics.core.shared_sovereignty.name")
    description = t_("content.culture.civics.core.shared_sovereignty.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
