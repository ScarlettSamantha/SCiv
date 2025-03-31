from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MilitaryEngineering(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.military_engineering",
            t_("tech.military_engineering.name"),
            t_("tech.military_engineering.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
