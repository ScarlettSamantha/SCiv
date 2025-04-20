from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Ballistics(Tech):
    key = "core.ballistics"
    name = t_("tech.ballistics.name")
    description = t_("tech.ballistics.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
