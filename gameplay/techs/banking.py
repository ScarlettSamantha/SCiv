from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Banking(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.banking",
            t_("tech.banking.name"),
            t_("tech.banking.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
