from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Castles(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.castles",
            t_("tech.castles.name"),
            t_("tech.castles.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
