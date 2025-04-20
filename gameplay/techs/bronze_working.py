from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class BronzeWorking(Tech):
    key = "core.bronze_working"
    name = t_("tech.bronze_working.name")
    description = t_("tech.bronze_working.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
