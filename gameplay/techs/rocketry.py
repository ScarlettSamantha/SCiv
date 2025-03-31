from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Rocketry(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.rocketry",
            t_("tech.rocketry.name"),
            t_("tech.rocketry.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
