from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Mathematics(Tech):
    key = "core.mathematics"
    name = t_("tech.mathematics.name")
    description = t_("tech.mathematics.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
