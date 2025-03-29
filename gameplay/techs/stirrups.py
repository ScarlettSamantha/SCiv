from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Stirrups(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.stirrups",
            t_("tech.stirrups.name"),
            t_("tech.stirrups.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
