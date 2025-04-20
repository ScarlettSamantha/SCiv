from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Steel(Tech):
    key = "core.steel"
    name = t_("tech.steel.name")
    description = t_("tech.steel.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
