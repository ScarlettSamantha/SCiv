from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Trapping(Tech):
    key = "core.trapping"
    name = t_("tech.trapping.name")
    description = t_("tech.trapping.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
