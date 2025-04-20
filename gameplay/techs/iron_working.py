from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class IronWorking(Tech):
    key = "core.iron_working"
    name = t_("tech.iron_working.name")
    description = t_("tech.iron_working.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
