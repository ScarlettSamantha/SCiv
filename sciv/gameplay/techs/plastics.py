from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Plastics(Tech):
    key = "core.plastics"
    name = t_("tech.plastics.name")
    description = t_("tech.plastics.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
