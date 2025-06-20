from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class AdvancedBallistics(Tech):
    key = "advanced_ballistics"
    name = t_("tech.advanced_ballistics.name")
    description = t_("tech.advanced_ballistics.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
