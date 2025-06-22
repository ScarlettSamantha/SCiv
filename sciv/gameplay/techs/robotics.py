from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Robotics(Tech):
    key = "core.robotics"
    name = t_("tech.robotics.name")
    description = t_("tech.robotics.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
