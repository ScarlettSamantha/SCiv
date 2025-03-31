from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Pottery(Tech):
    key = "core.pottery"
    name = t_("tech.pottery.name")
    description = t_("tech.pottery.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
