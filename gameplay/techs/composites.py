from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Composites(Tech):
    key = "core.composites"
    name = t_("tech.composites.name")
    description = t_("tech.composites.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
