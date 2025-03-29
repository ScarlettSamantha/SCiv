from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MilitaryScience(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.military_science",
            t_("tech.military_science.name"),
            t_("tech.military_science.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
