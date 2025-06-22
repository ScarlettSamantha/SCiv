from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Refining(Tech):
    key = "core.refining"
    name = t_("tech.refining.name")
    description = t_("tech.refining.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
