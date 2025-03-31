from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Robotics(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.robotics",
            t_("tech.robotics.name"),
            t_("tech.robotics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
