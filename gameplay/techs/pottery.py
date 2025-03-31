from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Pottery(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.pottery",
            t_("tech.pottery.name"),
            t_("tech.pottery.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
