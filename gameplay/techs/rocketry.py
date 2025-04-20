from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Rocketry(Tech):
    key = "core.rocketry"
    name = t_("tech.rocketry.name")
    description = t_("tech.rocketry.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
