from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Sanitation(Tech):
    key = "core.sanitation"
    name = t_("tech.sanitation.name")
    description = t_("tech.sanitation.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
