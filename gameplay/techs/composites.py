from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Composites(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.composites",
            t_("tech.composites.name"),
            t_("tech.composites.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
