from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Sailing(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.sailing",
            t_("tech.saling.name"),
            t_("tech.saling.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
