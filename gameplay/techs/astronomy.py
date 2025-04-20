from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Astronomy(Tech):
    key = "core.astronomy"
    name = t_("tech.astronomy.name")
    description = t_("tech.astronomy.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
