from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Writing(Tech):
    key = "core.writing"
    name = t_("tech.writing.name")
    description = t_("tech.writing.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
