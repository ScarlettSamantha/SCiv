from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Wheel(Tech):
    key = "core.wheel"
    name = t_("tech.wheel.name")
    description = t_("tech.wheel.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
