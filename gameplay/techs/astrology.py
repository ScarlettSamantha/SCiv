from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Astrology(Tech):
    key = "core.astrology"
    name = t_("tech.astrology.name")
    description = t_("tech.astrology.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
