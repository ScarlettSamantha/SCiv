from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class CombinedArms(Tech):
    key = "core.combined_arms"
    name = t_("tech.combined_arms.name")
    description = t_("tech.combined_arms.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
