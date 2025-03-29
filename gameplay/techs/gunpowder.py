from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Gunpowder(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.gunpowder",
            t_("tech.gunpowder.name"),
            t_("tech.gunpowder.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
