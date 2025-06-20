from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class SquareRigging(Tech):
    key = "core.square_rigging"
    name = t_("tech.square_rigging.name")
    description = t_("tech.square_rigging.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
