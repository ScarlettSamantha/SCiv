from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Construction(Tech):
    key = "core.construction"
    name = t_("tech.construction.name")
    description = t_("tech.construction.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
