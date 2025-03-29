from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Engineering(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.engineering",
            t_("tech.engineering.name"),
            t_("tech.engineering.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
