from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Rifling(Tech):
    key = "core.rifling"
    name = t_("tech.rifling.name")
    description = t_("tech.rifling.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
