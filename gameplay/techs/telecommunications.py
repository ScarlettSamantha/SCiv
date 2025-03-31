from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Telecommunications(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.telecommunications",
            t_("tech.telecommunications.name"),
            t_("tech.telecommunications.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
