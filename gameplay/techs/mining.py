from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Mining(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.mining",
            t_("tech.mining.name"),
            t_("tech.mining.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
