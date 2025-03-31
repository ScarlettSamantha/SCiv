from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Computers(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.computers",
            t_("tech.computers.name"),
            t_("tech.computers.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
