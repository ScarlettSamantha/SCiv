from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Rifling(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.rifling",
            t_("tech.rifling.name"),
            t_("tech.rifling.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
