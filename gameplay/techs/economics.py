from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Economics(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.economics",
            t_("tech.economics.name"),
            t_("tech.economics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
