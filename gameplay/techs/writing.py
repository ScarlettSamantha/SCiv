from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Writing(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.writing",
            t_("tech.writing.name"),
            t_("tech.writing.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
