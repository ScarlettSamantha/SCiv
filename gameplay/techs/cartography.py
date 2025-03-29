from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Cartography(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.cartography",
            t_("tech.cartography.name"),
            t_("tech.cartography.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
