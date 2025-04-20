from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Electricity(Tech):
    key = "core.electricity"
    name = t_("tech.electricity.name")
    description = t_("tech.electricity.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
