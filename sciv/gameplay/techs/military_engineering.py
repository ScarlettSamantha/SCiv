from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MilitaryEngineering(Tech):
    key = "core.military_engineering"
    name = t_("tech.military_engineering.name")
    description = t_("tech.military_engineering.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
