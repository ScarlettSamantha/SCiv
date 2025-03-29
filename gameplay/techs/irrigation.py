from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Irrigation(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.irrigation",
            t_("tech.irrigation.name"),
            t_("tech.irrigation.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
