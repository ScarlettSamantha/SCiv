from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class AdvancedBallistics(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.advanced_ballistics",
            t_("tech.advanced_ballistics.name"),
            t_("tech.advanced_ballistics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
