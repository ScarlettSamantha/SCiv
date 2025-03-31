from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MilitaryTactics(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.military_tactics",
            t_("tech.military_tactics.name"),
            t_("tech.military_tactics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
