from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Sailing(Tech):
    key = "core.sailing"
    name = t_("tech.sailing.name")
    description = t_("tech.sailing.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
