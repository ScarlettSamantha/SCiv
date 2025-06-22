from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Calendar(Tech):
    key = "core.calendar"
    name = t_("tech.calendar.name")
    description = t_("tech.calendar.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
