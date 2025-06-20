from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Combustion(Tech):
    key = "core.combustion"
    name = t_("tech.combustion.name")
    description = t_("tech.combustion.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
