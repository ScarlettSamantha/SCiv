from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Steel(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.steel",
            t_("tech.steel.name"),
            t_("tech.steel.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
