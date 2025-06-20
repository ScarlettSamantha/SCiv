from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Stirrups(Tech):
    key = "core.stirrups"
    name = t_("tech.stirrups.name")
    description = t_("tech.stirrups.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
