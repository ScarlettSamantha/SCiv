from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class IronWorking(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.iron_working",
            t_("tech.iron_working.name"),
            t_("tech.iron_working.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
