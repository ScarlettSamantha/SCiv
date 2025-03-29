from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Chemistry(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.chemistry",
            t_("tech.chemistry.name"),
            t_("tech.chemistry.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
