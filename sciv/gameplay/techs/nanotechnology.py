from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Nanotechnology(Tech):
    key = "core.nanotechnology"
    name = t_("tech.nanotechnology.name")
    description = t_("tech.nanotechnology.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
