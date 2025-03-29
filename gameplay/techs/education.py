from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Education(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.education",
            t_("tech.education.name"),
            t_("tech.education.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
