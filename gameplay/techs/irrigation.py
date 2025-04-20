from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Irrigation(Tech):
    key = "core.irrigation"
    name = t_("tech.irrigation.name")
    description = t_("tech.irrigation.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
