from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Nanotechnology(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.nanotechnology",
            t_("tech.nanotechnology.name"),
            t_("tech.nanotechnology.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
