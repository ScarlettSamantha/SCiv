from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Education(Tech):
    key = "core.education"
    name = t_("tech.education.name")
    description = t_("tech.education.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
