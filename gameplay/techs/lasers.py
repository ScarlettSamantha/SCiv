from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Lasers(Tech):
    key = "core.lasers"
    name = t_("tech.lasers.name")
    description = t_("tech.lasers.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
