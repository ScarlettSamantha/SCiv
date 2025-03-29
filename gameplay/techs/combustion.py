from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Combustion(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.combustion",
            t_("tech.combustion.name"),
            t_("tech.combustion.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
