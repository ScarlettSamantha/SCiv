from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Cartography(Tech):
    key = "core.cartography"
    name = t_("tech.cartography.name")
    description = t_("tech.cartography.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
