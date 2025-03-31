from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Mining(Tech):
    key = "core.mining"
    name = t_("tech.mining.name")
    description = t_("tech.mining.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
