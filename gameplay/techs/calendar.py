from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Calendar(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.calendar",
            t_("tech.calendar.name"),
            t_("tech.calendar.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
