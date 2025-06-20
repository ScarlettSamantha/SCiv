from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MilitaryTactics(Tech):
    key = "core.military_tactics"
    name = t_("tech.military_tactics.name")
    description = t_("tech.military_tactics.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
