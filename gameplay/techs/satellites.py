from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Satellites(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.satellites",
            t_("tech.satellites.name"),
            t_("tech.satellites.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
