from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Economics(Tech):
    key = "core.economics"
    name = t_("tech.economics.name")
    description = t_("tech.economics.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
