from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Banking(Tech):
    key = "core.banking"
    name = t_("tech.banking.name")
    description = t_("tech.banking.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
