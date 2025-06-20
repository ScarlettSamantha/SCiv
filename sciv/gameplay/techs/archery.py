from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Archery(Tech):
    key = "core.archery"
    name = t_("tech.archery.name")
    description = t_("tech.archery.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
