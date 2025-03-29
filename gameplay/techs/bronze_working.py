from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class BronzeWorking(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.bronze_working",
            t_("tech.bronze_working.name"),
            t_("tech.bronze_working.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
