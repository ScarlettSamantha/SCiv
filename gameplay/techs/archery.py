from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Archery(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.archery",
            t_("tech.archery.name"),
            t_("tech.archery.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
