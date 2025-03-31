from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Satellites(Tech):
    key = "core.satellites"
    name = t_("tech.satellites.name")
    description = t_("tech.satellites.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
