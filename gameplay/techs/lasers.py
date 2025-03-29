from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Lasers(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.lasers",
            t_("tech.lasers.name"),
            t_("tech.lasers.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
