from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Gunpowder(Tech):
    key = "core.gunpowder"
    name = t_("tech.gunpowder.name")
    description = t_("tech.gunpowder.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
