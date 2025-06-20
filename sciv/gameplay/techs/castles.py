from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Castles(Tech):
    key = "core.castles"
    name = t_("tech.castles.name")
    description = t_("tech.castles.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
