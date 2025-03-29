from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Astronomy(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.astronomy",
            t_("tech.astronomy.name"),
            t_("tech.astronomy.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
