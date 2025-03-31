from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Mathematics(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.mathematics",
            t_("tech.mathematics.name"),
            t_("tech.mathematics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
